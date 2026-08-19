"""Answers "is this person/team actually getting better at prompting" --
not just "what's their score right now." Compares a recent window of scored
prompts against the window before it, per GCCF dimension, and surfaces the
single most common reason a dimension is still weak, with its tip. Shared
by GET /users/{id}/progress and GET /teams/{id}/progress so a user's
progress and their team's progress are computed the exact same way.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from psycopg import AsyncConnection

DIMENSION_LABELS = {"goal": "Goal", "context": "Context", "constraints": "Constraints", "format": "Format"}
_FLAT_BAND = 3.0  # a delta smaller than this in either direction reads as noise, not progress
_WEAK_ENOUGH_FOR_ISSUE = 65.0  # only count an issue toward "most common" below this score
WINDOW = 15


@dataclass(frozen=True)
class DimensionProgressResult:
    dimension: str
    recent_avg: float | None
    prior_avg: float | None
    delta: float | None
    direction: str
    sample_size: int
    most_common_issue: str | None
    most_common_issue_message: str | None
    tip: str | None


async def _fetch_scored_rows(conn: AsyncConnection, where_clause: str, params: tuple) -> list[tuple]:
    async with conn.cursor() as cur:
        await cur.execute(
            f"""
            SELECT ps.goal_score, ps.context_score, ps.constraints_score, ps.format_score,
                   ps.dimension_feedback, p.submitted_at
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            JOIN users u ON u.id = p.user_id
            {where_clause}
            AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
            ORDER BY p.submitted_at DESC
            """,
            params,
        )
        return await cur.fetchall()


def _direction(delta: float | None) -> str:
    if delta is None:
        return "flat"
    if delta > _FLAT_BAND:
        return "improving"
    if delta < -_FLAT_BAND:
        return "declining"
    return "flat"


_DIM_INDEX = {"goal": 0, "context": 1, "constraints": 2, "format": 3}


def _compute_dimension(dimension: str, recent: list[tuple], prior: list[tuple]) -> DimensionProgressResult:
    idx = _DIM_INDEX[dimension]

    recent_avg = round(sum(r[idx] for r in recent) / len(recent), 2) if recent else None
    prior_avg = round(sum(r[idx] for r in prior) / len(prior), 2) if prior else None
    delta = round(recent_avg - prior_avg, 2) if (recent_avg is not None and prior_avg is not None) else None

    codes: list[str] = []
    messages: dict[str, str] = {}
    tips: dict[str, str] = {}
    for row in recent:
        if row[idx] >= _WEAK_ENOUGH_FOR_ISSUE:
            continue
        fb = (row[4] or {}).get(dimension) or {}
        for issue in fb.get("issue_detail") or []:
            codes.append(issue["code"])
            messages.setdefault(issue["code"], issue["message"])
            tips.setdefault(issue["code"], issue["tip"])

    most_common_issue = most_common_message = tip = None
    if codes:
        top_code, _ = Counter(codes).most_common(1)[0]
        most_common_issue = top_code
        most_common_message = messages.get(top_code)
        tip = tips.get(top_code)

    return DimensionProgressResult(
        dimension=dimension,
        recent_avg=recent_avg,
        prior_avg=prior_avg,
        delta=delta,
        direction=_direction(delta),
        sample_size=len(recent),
        most_common_issue=most_common_issue,
        most_common_issue_message=most_common_message,
        tip=tip,
    )


def _headline(dimensions: list[DimensionProgressResult], scope_label: str) -> tuple[str, str | None, str | None]:
    scored = [d for d in dimensions if d.recent_avg is not None]
    if not scored:
        return f"{scope_label} hasn't submitted enough scored prompts yet for a progress read.", None, None

    strongest = max(scored, key=lambda d: d.recent_avg)
    weakest = min(scored, key=lambda d: d.recent_avg)
    improving = [d for d in dimensions if d.direction == "improving"]

    parts = [f"{scope_label} is strongest at {DIMENSION_LABELS[strongest.dimension]} ({strongest.recent_avg:.0f}/100)."]
    if improving:
        best_mover = max(improving, key=lambda d: d.delta or 0)
        parts.append(f"{DIMENSION_LABELS[best_mover.dimension]} is trending up (+{best_mover.delta:.0f}).")
    if weakest.dimension != strongest.dimension:
        tail = f"{DIMENSION_LABELS[weakest.dimension]} is the growth area ({weakest.recent_avg:.0f}/100)"
        if weakest.most_common_issue_message:
            tail += f" -- most often because it {weakest.most_common_issue_message}"
        parts.append(tail + ".")

    return " ".join(parts), strongest.dimension, weakest.dimension


async def compute_progress(
    conn: AsyncConnection, where_clause: str, params: tuple, scope: str, scope_label: str
) -> dict:
    """`where_clause` must be a `WHERE ...` fragment scoping to one user
    (`WHERE p.user_id = %s`) or one team (`WHERE u.team_id = %s`) -- the base
    query already joins `users u ON u.id = p.user_id` so either scoping
    column is available."""
    rows = await _fetch_scored_rows(conn, where_clause, params)
    recent, prior = rows[:WINDOW], rows[WINDOW : WINDOW * 2]

    dimensions = [_compute_dimension(dim, recent, prior) for dim in DIMENSION_LABELS]
    headline, strongest, weakest = _headline(dimensions, scope_label)

    return {
        "scope": scope,
        "scope_label": scope_label,
        "dimensions": dimensions,
        "strongest_dimension": strongest,
        "weakest_dimension": weakest,
        "headline": headline,
    }
