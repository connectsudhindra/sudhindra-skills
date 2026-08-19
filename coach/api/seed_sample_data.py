#!/usr/bin/env python3
"""Populates the database with realistic sample teams, users, and 30 days of
prompt history, so the dashboard has something worth looking at before any
real usage has accumulated.

Run inside the api container, where psycopg and DATABASE_URL are already
set up:

    docker compose exec api python seed_sample_data.py
    docker compose exec api python seed_sample_data.py --wipe   # clear existing sample data first

Deliberately NOT part of docker-entrypoint-initdb.d -- sample data should
never silently appear in a real install, only when explicitly asked for.
Every row this script creates is tagged (`users.email` ends in
`@sample.coach.local`), so --wipe can remove exactly this data and nothing
a real user created.
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import psycopg

import config

SAMPLE_EMAIL_SUFFIX = "@sample.coach.local"
ROLLING_WINDOW = config.ROLLING_WINDOW_SIZE
MIN_PROMPTS_TO_LEVEL = config.MIN_SCORABLE_PROMPTS_TO_LEVEL

PROMPT_TEMPLATES_WEAK = [
    "fix the bug",
    "make it work",
    "help with the api",
    "the tests are failing",
    "improve performance",
    "update the component",
]
PROMPT_TEMPLATES_STRONG = [
    "Fix the race condition in src/workers/queue.py when two consumers claim the same job. "
    "Error: \"IntegrityError: duplicate key value\". Don't change the public claim_job() signature. "
    "Return as a diff.",
    "Refactor src/billing/invoice.py to extract the tax calculation into its own function. "
    "Must not change the rounding behavior. Respond with a short summary of what moved.",
    "Add retry logic to the upload handler in src/uploads/client.py, at most 3 attempts, "
    "exponential backoff. Don't touch the existing error logging. Return as a diff.",
    "Investigate why src/api/routes/orders.py throws \"KeyError: total\" when the cart is empty. "
    "Keep the existing validation middleware unchanged. Explain the root cause in a short paragraph, "
    "then propose a fix as a diff.",
    "Write a test for get_user_by_id in src/services/user_service.py covering the missing-id case. "
    "Only test the public interface, no mocking internals. Format as a single pytest function.",
]


@dataclass
class UserProfile:
    name: str
    email_local: str
    trajectory: str  # "flat_weak" | "improving" | "strong_steady" | "dip_recover"
    prompt_count: int = 45
    days_span: int = 28


@dataclass
class TeamSeed:
    name: str
    users: list[UserProfile] = field(default_factory=list)


TEAMS = [
    TeamSeed(
        name="Platform",
        users=[
            UserProfile("Priya Nair", "priya.nair", "strong_steady"),
            UserProfile("Marcus Webb", "marcus.webb", "improving"),
            UserProfile("Jae Park", "jae.park", "flat_weak"),
            UserProfile("Sofia Alvarez", "sofia.alvarez", "dip_recover"),
        ],
    ),
    TeamSeed(
        name="Growth",
        users=[
            UserProfile("Liam O'Connor", "liam.oconnor", "improving"),
            UserProfile("Amara Okafor", "amara.okafor", "strong_steady"),
            UserProfile("Ben Torres", "ben.torres", "flat_weak"),
        ],
    ),
    TeamSeed(
        name="Data",
        users=[
            UserProfile("Yuki Tanaka", "yuki.tanaka", "strong_steady"),
            UserProfile("Devon Clarke", "devon.clarke", "dip_recover"),
            UserProfile("Nina Petrov", "nina.petrov", "improving"),
            UserProfile("Sam Osei", "sam.osei", "flat_weak"),
        ],
    ),
]


def target_composite_for_day(trajectory: str, day_fraction: float, rng: random.Random) -> float:
    """day_fraction is 0.0 (first day) to 1.0 (most recent day)."""
    noise = rng.uniform(-8, 8)
    if trajectory == "flat_weak":
        base = 25
    elif trajectory == "strong_steady":
        base = 90
    elif trajectory == "improving":
        base = 20 + day_fraction * 65  # 20 -> 85
    elif trajectory == "dip_recover":
        # dips hard around the midpoint, recovers by the end
        dip = -35 * max(0.0, 1 - abs(day_fraction - 0.5) * 4)
        base = 70 + dip
    else:
        base = 50
    return max(2.0, min(98.0, base + noise))


def scores_for_composite(composite: float, rng: random.Random) -> tuple[float, float, float, float]:
    """Four dimension scores that average to roughly `composite`, with a bit
    of spread so the radar chart shows real dimensional variance rather than
    a perfect square."""
    spread = 12
    raw = [composite + rng.uniform(-spread, spread) for _ in range(4)]
    raw = [max(0.0, min(100.0, v)) for v in raw]
    # nudge the mean back toward the target composite
    delta = composite - sum(raw) / 4
    raw = [max(0.0, min(100.0, v + delta)) for v in raw]
    return tuple(round(v, 2) for v in raw)  # type: ignore[return-value]


def prompt_text_for(composite: float, rng: random.Random) -> str:
    pool = PROMPT_TEMPLATES_STRONG if composite >= 55 else PROMPT_TEMPLATES_WEAK
    return rng.choice(pool)


def level_for_score(cur: psycopg.Cursor, composite: float) -> tuple[int, str]:
    cur.execute(
        "SELECT level_num, name FROM levels WHERE min_score <= %s ORDER BY level_num DESC LIMIT 1",
        (composite,),
    )
    return cur.fetchone()


def seed_user(cur: psycopg.Cursor, team_id: str, profile: UserProfile, rng: random.Random) -> None:
    email = f"{profile.email_local}{SAMPLE_EMAIL_SUFFIX}"
    cur.execute(
        "INSERT INTO users (name, email, team_id, coaching_mode) VALUES (%s, %s, %s, 'in_session') "
        "RETURNING id",
        (profile.name, email, team_id),
    )
    (user_id,) = cur.fetchone()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=profile.days_span)

    # A handful of sessions across the span, prompts distributed across them.
    session_count = max(4, profile.prompt_count // 10)
    session_ids = []
    for s in range(session_count):
        session_day_offset = (profile.days_span * s) / max(1, session_count - 1)
        session_start = start + timedelta(days=session_day_offset, hours=rng.uniform(0, 6))
        cur.execute(
            "INSERT INTO sessions (user_id, claude_session_id, started_at, ended_at) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (
                user_id,
                f"sample-{profile.email_local}-{s}",
                session_start,
                session_start + timedelta(minutes=rng.uniform(15, 90)),
            ),
        )
        (session_id,) = cur.fetchone()
        session_ids.append((session_id, session_start))

    current_level = 1
    rolling_scores: list[float] = []

    for i in range(profile.prompt_count):
        day_fraction = i / max(1, profile.prompt_count - 1)
        session_id, session_start = session_ids[min(i * session_count // profile.prompt_count, session_count - 1)]
        submitted_at = session_start + timedelta(minutes=rng.uniform(0, 60))

        composite = target_composite_for_day(profile.trajectory, day_fraction, rng)
        goal, context, constraints, fmt = scores_for_composite(composite, rng)
        text = prompt_text_for(composite, rng)

        cur.execute(
            "INSERT INTO prompts (session_id, user_id, prompt_text, is_scorable, submitted_at) "
            "VALUES (%s, %s, %s, true, %s) RETURNING id",
            (session_id, user_id, text, submitted_at),
        )
        (prompt_id,) = cur.fetchone()
        cur.execute(
            "INSERT INTO prompt_scores "
            "(prompt_id, scoring_method, goal_score, context_score, constraints_score, format_score, scored_at) "
            "VALUES (%s, 'heuristic', %s, %s, %s, %s, %s)",
            (prompt_id, goal, context, constraints, fmt, submitted_at),
        )

        rolling_scores.append(round((goal + context + constraints + fmt) / 4, 2))
        if len(rolling_scores) > ROLLING_WINDOW:
            rolling_scores.pop(0)

        cur.execute("UPDATE prompts SET level_at_submission = %s WHERE id = %s", (current_level, prompt_id))

        if len(rolling_scores) >= MIN_PROMPTS_TO_LEVEL:
            avg = sum(rolling_scores) / len(rolling_scores)
            earned_level, _ = level_for_score(cur, avg)
            if earned_level > current_level:
                current_level = earned_level
                cur.execute(
                    "INSERT INTO level_history (user_id, level_num, achieved_at) VALUES (%s, %s, %s)",
                    (user_id, current_level, submitted_at),
                )

    cur.execute("UPDATE users SET current_level = %s WHERE id = %s", (current_level, user_id))

    # Close the most recent session with a session_level, and (for two
    # profiles) leave one end-of-session coaching_feedback row so the UI's
    # feedback panel has something real to show.
    last_session_id, _ = session_ids[-1]
    cur.execute(
        "SELECT AVG(ps.composite_score) FROM prompt_scores ps JOIN prompts p ON p.id = ps.prompt_id "
        "WHERE p.session_id = %s",
        (last_session_id,),
    )
    (last_avg,) = cur.fetchone()
    if last_avg is not None:
        session_level, _ = level_for_score(cur, float(last_avg))
        cur.execute("UPDATE sessions SET session_level = %s WHERE id = %s", (session_level, last_session_id))

    if profile.trajectory in ("improving", "dip_recover"):
        weakest = min(
            [("Goal", goal), ("Context", context), ("Constraints", constraints), ("Format", fmt)],
            key=lambda pair: pair[1],
        )
        cur.execute(
            "INSERT INTO coaching_feedback (session_id, user_id, feedback_type, feedback_text, created_at) "
            "VALUES (%s, %s, 'end_of_session', %s, %s)",
            (
                last_session_id,
                user_id,
                f"Last session: average GCCF {last_avg:.0f}/100. Weakest dimension: {weakest[0]} "
                f"({weakest[1]:.0f}/100).",
                submitted_at,
            ),
        )


def wipe_sample_data(cur: psycopg.Cursor) -> None:
    cur.execute(
        "SELECT id FROM users WHERE email LIKE %s", (f"%{SAMPLE_EMAIL_SUFFIX}",)
    )
    user_ids = [r[0] for r in cur.fetchall()]
    if not user_ids:
        return
    cur.execute(
        "DELETE FROM coaching_feedback WHERE user_id = ANY(%s)", (user_ids,)
    )
    cur.execute(
        "DELETE FROM prompt_scores WHERE prompt_id IN (SELECT id FROM prompts WHERE user_id = ANY(%s))",
        (user_ids,),
    )
    cur.execute("DELETE FROM prompts WHERE user_id = ANY(%s)", (user_ids,))
    cur.execute("DELETE FROM level_history WHERE user_id = ANY(%s)", (user_ids,))
    cur.execute("DELETE FROM sessions WHERE user_id = ANY(%s)", (user_ids,))
    cur.execute("DELETE FROM users WHERE id = ANY(%s)", (user_ids,))
    # Only remove sample teams that are now empty -- a real user could have
    # joined one of these team names in the meantime, and shouldn't lose it.
    team_names = [t.name for t in TEAMS]
    cur.execute(
        "DELETE FROM teams WHERE name = ANY(%s) "
        "AND id NOT IN (SELECT DISTINCT team_id FROM users WHERE team_id IS NOT NULL)",
        (team_names,),
    )
    print(f"Wiped {len(user_ids)} sample user(s) and their data.")


def main() -> int:
    wipe = "--wipe" in sys.argv

    rng = random.Random(20260819)  # fixed seed -- reproducible sample data

    with psycopg.connect(config.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            if wipe:
                wipe_sample_data(cur)
                if "--wipe-only" in sys.argv:
                    return 0

            for team in TEAMS:
                cur.execute(
                    "INSERT INTO teams (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name "
                    "RETURNING id",
                    (team.name,),
                )
                (team_id,) = cur.fetchone()

                for profile in team.users:
                    email = f"{profile.email_local}{SAMPLE_EMAIL_SUFFIX}"
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cur.fetchone():
                        print(f"Skipping {email} -- already exists (use --wipe to reset sample data first).")
                        continue
                    seed_user(cur, team_id, profile, rng)
                    print(f"Seeded {profile.name} ({team.name}, {profile.trajectory}).")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
