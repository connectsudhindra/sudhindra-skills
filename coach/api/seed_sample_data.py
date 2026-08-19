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

Prompt text is assembled from real components (a verb, an artifact, error
detail, framing, scope, a requirement, a format ask), each included with a
probability driven by a per-day "quality" target, then scored through the
*real* heuristic scorer (scoring/heuristic.py) -- not hand-picked numbers.
That's what makes the dimension_feedback, issue codes, and progress
insights on seeded users mean something: they're the same pipeline real
usage goes through, just with generated instead of typed text.
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Json

import config
from scoring.heuristic import score_prompt

SAMPLE_EMAIL_SUFFIX = "@sample.coach.local"
ROLLING_WINDOW = config.ROLLING_WINDOW_SIZE
MIN_PROMPTS_TO_LEVEL = config.MIN_SCORABLE_PROMPTS_TO_LEVEL

_VERBS = ["Fix", "Add", "Refactor", "Investigate", "Update", "Remove", "Optimize"]
_WEAK_VERBS = ["look at", "handle", "deal with"]
_ARTIFACTS = [
    "the login handler in `src/auth/login.py`",
    "the checkout flow in `src/checkout/cart.py`",
    "the retry logic in `src/uploads/client.py`",
    "the invoice calculation in `src/billing/invoice.py`",
    "the query builder in `src/db/query.py`",
    "the websocket handler in `src/realtime/socket.py`",
]
_ERROR_DETAILS = [
    'It throws "KeyError: total" when the cart is empty.',
    'Error: "AttributeError: NoneType has no attribute email".',
    'It throws "IntegrityError: duplicate key value".',
    'Logs show "TimeoutError after 30s".',
]
_FRAMINGS = [
    "when the cart is empty",
    "after the recent schema migration",
    "given a missing id",
    "when two requests race",
]
_SCOPES = [
    "Don't change the public API.",
    "Keep the existing validation unchanged.",
    "Don't touch the error logging.",
]
_REQUIREMENTS = [
    "Must not exceed 3 retries.",
    "Should preserve backward compatibility.",
    "Must complete within 200ms.",
]
_FORMAT_ASKS = [
    "Return as a diff.",
    "Respond with a short summary.",
    "Format as a checklist.",
]
_WEAK_FALLBACKS = ["fix it", "help", "make it work", "the tests are failing", "improve performance", "update the thing"]


def build_prompt_text(quality: float, rng: random.Random) -> str:
    """quality in [0, 1] -- probabilistically includes more GCCF-bearing
    clauses as it rises. Not a target score; the real scorer decides that."""
    quality = max(0.0, min(1.0, quality))
    if quality < 0.12 and rng.random() < 0.6:
        return rng.choice(_WEAK_FALLBACKS)

    has_verb = rng.random() < min(1.0, quality + 0.35)
    has_artifact = rng.random() < min(1.0, quality + 0.25)
    has_detail = rng.random() < quality
    has_framing = rng.random() < max(0.0, quality - 0.1)
    has_scope = rng.random() < max(0.0, quality - 0.15)
    has_requirement = rng.random() < max(0.0, quality - 0.2)
    has_format = rng.random() < max(0.0, quality - 0.05)

    verb = rng.choice(_VERBS) if has_verb else rng.choice(_WEAK_VERBS)
    artifact = rng.choice(_ARTIFACTS) if has_artifact else "it"

    sentence = f"{verb} {artifact}"
    if has_framing:
        sentence += f" {rng.choice(_FRAMINGS)}"
    sentence += "."
    if has_detail:
        sentence += " " + rng.choice(_ERROR_DETAILS)
    if has_scope:
        sentence += " " + rng.choice(_SCOPES)
    if has_requirement:
        sentence += " " + rng.choice(_REQUIREMENTS)
    if has_format:
        sentence += " " + rng.choice(_FORMAT_ASKS)

    return sentence


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


def target_quality_for_day(trajectory: str, day_fraction: float, rng: random.Random) -> float:
    """day_fraction is 0.0 (first day) to 1.0 (most recent day). Returned
    value drives build_prompt_text's clause-inclusion probabilities."""
    noise = rng.uniform(-0.08, 0.08)
    if trajectory == "flat_weak":
        base = 0.22
    elif trajectory == "strong_steady":
        base = 0.85
    elif trajectory == "improving":
        base = 0.15 + day_fraction * 0.65  # weak -> strong
    elif trajectory == "dip_recover":
        dip = -0.35 * max(0.0, 1 - abs(day_fraction - 0.5) * 4)
        base = 0.65 + dip
    else:
        base = 0.45
    return max(0.0, min(0.98, base + noise))


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
    last_score = None

    for i in range(profile.prompt_count):
        day_fraction = i / max(1, profile.prompt_count - 1)
        session_id, session_start = session_ids[min(i * session_count // profile.prompt_count, session_count - 1)]
        submitted_at = session_start + timedelta(minutes=rng.uniform(0, 60))

        quality = target_quality_for_day(profile.trajectory, day_fraction, rng)
        text = build_prompt_text(quality, rng)
        score = score_prompt(text)  # the real scorer -- authentic scores + dimension_feedback
        last_score = score

        cur.execute(
            "INSERT INTO prompts (session_id, user_id, prompt_text, is_scorable, submitted_at) "
            "VALUES (%s, %s, %s, true, %s) RETURNING id",
            (session_id, user_id, text, submitted_at),
        )
        (prompt_id,) = cur.fetchone()
        cur.execute(
            "INSERT INTO prompt_scores "
            "(prompt_id, scoring_method, goal_score, context_score, constraints_score, format_score, "
            "rationale, dimension_feedback, scored_at) "
            "VALUES (%s, 'heuristic', %s, %s, %s, %s, %s, %s, %s)",
            (
                prompt_id, score.goal, score.context, score.constraints, score.format,
                score.rationale, Json(score.dimensions_json()), submitted_at,
            ),
        )

        # Roughly 40% of prompts also get a synthetic LLM score, so the
        # Scoring Comparison panel has real-looking data without needing a
        # funded ANTHROPIC_API_KEY. Jittered close to the heuristic scores
        # (an LLM judge and a decent heuristic should mostly agree), with
        # occasional larger divergence -- a flat 1:1 match would misrepresent
        # what real agreement looks like.
        if rng.random() < 0.4:
            llm_jitter = 15 if rng.random() < 0.15 else 6
            llm_goal = max(0.0, min(100.0, score.goal + rng.uniform(-llm_jitter, llm_jitter)))
            llm_context = max(0.0, min(100.0, score.context + rng.uniform(-llm_jitter, llm_jitter)))
            llm_constraints = max(0.0, min(100.0, score.constraints + rng.uniform(-llm_jitter, llm_jitter)))
            llm_format = max(0.0, min(100.0, score.format + rng.uniform(-llm_jitter, llm_jitter)))
            cur.execute(
                "INSERT INTO prompt_scores "
                "(prompt_id, scoring_method, model_name, goal_score, context_score, constraints_score, "
                "format_score, rationale, latency_ms, scored_at) "
                "VALUES (%s, 'llm', %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    prompt_id,
                    "claude-haiku-4-5-20251001 (simulated for sample data)",
                    round(llm_goal, 2),
                    round(llm_context, 2),
                    round(llm_constraints, 2),
                    round(llm_format, 2),
                    "Simulated score for sample data -- not a real model call.",
                    int(rng.uniform(280, 650)),
                    submitted_at,
                ),
            )

        rolling_scores.append(score.composite)
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

    # Close every session with its own session_level (not just the last
    # one) -- the Sessions view shows this per session, so a blank level on
    # every historical row but the newest would look broken.
    last_avg = None
    for sid, _ in session_ids:
        cur.execute(
            "SELECT AVG(ps.composite_score) FROM prompt_scores ps JOIN prompts p ON p.id = ps.prompt_id "
            "WHERE p.session_id = %s AND ps.scoring_method = 'heuristic'",
            (sid,),
        )
        (avg,) = cur.fetchone()
        if avg is not None:
            session_level, _ = level_for_score(cur, float(avg))
            cur.execute("UPDATE sessions SET session_level = %s WHERE id = %s", (session_level, sid))
            last_avg = avg
    last_session_id, _ = session_ids[-1]

    if profile.trajectory in ("improving", "dip_recover") and last_score is not None:
        weakest_dim = min(last_score.dimensions.values(), key=lambda fb: fb.score)
        weakest_label = next(k for k, v in last_score.dimensions.items() if v is weakest_dim).capitalize()
        detail = f" -- most often because it {weakest_dim.message}" if weakest_dim.issues else ""
        cur.execute(
            "INSERT INTO coaching_feedback (session_id, user_id, feedback_type, feedback_text, created_at) "
            "VALUES (%s, %s, 'end_of_session', %s, %s)",
            (
                last_session_id,
                user_id,
                f"Last session: average GCCF {last_avg:.0f}/100. Weakest dimension: {weakest_label} "
                f"({weakest_dim.score:.0f}/100){detail}.",
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
