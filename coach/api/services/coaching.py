"""Turns scores into the actual words a user sees -- both the in-session
block reason and the end-of-session summary. Kept separate from
level_engine.py: that module decides *what level you're at*, this one
decides *what to say about it*.
"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from scoring.heuristic import GCCFScore

if TYPE_CHECKING:
    # block_reason() below has no DB dependency at all -- it's imported
    # directly by coach/hooks/on_prompt_submit.py, which must run with
    # nothing but a system python3, no psycopg installed. Only
    # compose_end_of_session_summary() (API-side only) needs a real
    # connection, so the import stays type-checking-only here.
    from psycopg import AsyncConnection

_DIMENSION_LABELS = (
    ("goal", "Goal"),
    ("context", "Context"),
    ("constraints", "Constraints"),
    ("format", "Format"),
)


def block_reason(score: GCCFScore, block_floor: float) -> str:
    """Plain-text reason shown to the user when UserPromptSubmit blocks a
    prompt. This IS the coaching -- there's no richer channel available to a
    hook (see coach/README.md for why). Resubmitting the same text passes
    through unblocked; see coach/hooks/on_prompt_submit.py. Every weak or
    developing dimension gets its specific issue plus the one thing to fix
    -- not just a checkmark, a next step."""
    lines = [
        f"This prompt scored {score.composite:.0f}/100 on GCCF (floor: {block_floor:.0f}). "
        "Sharpen it, or send it again unchanged to proceed anyway.",
        "",
    ]
    for attr, label in _DIMENSION_LABELS:
        value = getattr(score, attr)
        fb = score.dimensions.get(attr) if score.dimensions else None
        mark = "✓" if value >= 60 else "✗"
        lines.append(f"  {mark} {label}: {value:.0f}/100")
        if fb is not None and fb.top_tip and value < 60:
            lines.append(f"      → {fb.top_tip}")
    return "\n".join(lines)


def _issue_summary(dimension_feedback_rows: list[dict], dimension: str) -> tuple[str | None, str | None]:
    """Most frequent issue code for one dimension across a batch of stored
    dimension_feedback JSON blobs, with that specific issue's own message
    (not the dimension's combined message). None if the dimension was never
    weak enough to log an issue in this batch."""
    codes: list[str] = []
    messages: dict[str, str] = {}
    for row in dimension_feedback_rows:
        dim = (row or {}).get(dimension) or {}
        for issue in dim.get("issue_detail") or []:
            codes.append(issue["code"])
            messages.setdefault(issue["code"], issue["message"])
    if not codes:
        return None, None
    top_code, _ = Counter(codes).most_common(1)[0]
    return top_code, messages.get(top_code)


async def compose_end_of_session_summary(
    conn: AsyncConnection, user_id: str, session_id: str
) -> str | None:
    """Called from the detached end-of-session worker (or the stale-session
    sweep) once a session has closed. Returns None if there's nothing
    scorable to summarize -- callers should skip inserting coaching_feedback
    in that case rather than send an empty summary."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT ps.goal_score, ps.context_score, ps.constraints_score, ps.format_score,
                   ps.composite_score, ps.dimension_feedback
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            WHERE p.session_id = %s AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
            """,
            (session_id,),
        )
        rows = await cur.fetchall()
        if not rows:
            return None

        n = len(rows)
        avg_goal = sum(r[0] for r in rows) / n
        avg_context = sum(r[1] for r in rows) / n
        avg_constraints = sum(r[2] for r in rows) / n
        avg_format = sum(r[3] for r in rows) / n
        avg_composite = sum(r[4] for r in rows) / n
        feedback_blobs = [r[5] for r in rows if r[5]]

        await cur.execute(
            "SELECT current_level, name, next_level_tip FROM users "
            "JOIN levels ON levels.level_num = users.current_level WHERE users.id = %s",
            (user_id,),
        )
        level_num, level_name, tip = await cur.fetchone()

        by_dim = {"goal": avg_goal, "context": avg_context, "constraints": avg_constraints, "format": avg_format}
        weakest_key, weakest_value = min(by_dim.items(), key=lambda pair: pair[1])
        weakest_label = dict(_DIMENSION_LABELS)[weakest_key]

        issue_code, issue_message = _issue_summary(feedback_blobs, weakest_key)

    lines = [
        f"Last session: {n} scored prompt(s), average GCCF {avg_composite:.0f}/100 "
        f"(you're at level {level_num} -- {level_name}).",
        f"Weakest dimension: {weakest_label} ({weakest_value:.0f}/100)"
        + (f" -- most often because it {issue_message}." if issue_message else "."),
    ]
    if tip:
        lines.append(f"Next up: {tip}")
    return " ".join(lines)
