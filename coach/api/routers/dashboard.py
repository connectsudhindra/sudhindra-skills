from __future__ import annotations

from fastapi import APIRouter, Query
from psycopg.rows import dict_row

import db
import schemas

router = APIRouter()


@router.get("/dashboard/level-distribution")
async def level_distribution() -> list[dict]:
    """How many users sit at each level -- the Team Roster's filter chips
    are driven by this, so counts are visible before a manager picks one."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT l.level_num, l.name, count(u.id) AS user_count
            FROM levels l
            LEFT JOIN users u ON u.current_level = l.level_num
            GROUP BY l.level_num, l.name
            ORDER BY l.level_num
            """
        )
        return await cur.fetchall()


@router.get("/dashboard/scoring-comparison")
async def scoring_comparison() -> dict:
    """Heuristic vs. LLM agreement across every prompt that has both --
    backs the Scoring Comparison panel. mean_abs_diff close to 0 means the
    cheap heuristic scorer is tracking the LLM well; a large value is a sign
    the heuristic's rules need tuning."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
              h.composite_score AS heuristic_composite,
              m.composite_score AS llm_composite,
              abs(h.composite_score - m.composite_score) AS abs_diff
            FROM prompt_scores h
            JOIN prompt_scores m
              ON m.prompt_id = h.prompt_id AND m.scoring_method = 'llm'
            WHERE h.scoring_method = 'heuristic'
            """
        )
        rows = await cur.fetchall()

    if not rows:
        return {"sample_size": 0, "mean_abs_diff": None, "pairs": []}

    mean_abs_diff = round(sum(float(r["abs_diff"]) for r in rows) / len(rows), 2)
    return {
        "sample_size": len(rows),
        "mean_abs_diff": mean_abs_diff,
        "pairs": [
            {
                "heuristic_composite": float(r["heuristic_composite"]),
                "llm_composite": float(r["llm_composite"]),
            }
            for r in rows
        ],
    }


@router.get("/dashboard/trend", response_model=schemas.TrendResponse)
async def trend(
    team_id: str | None = Query(default=None), days: int = Query(default=30, le=180)
) -> schemas.TrendResponse:
    """Daily average GCCF composite over the trailing `days` -- backs the
    trend chart on Team Roster (org-wide, no team_id) and the Teams
    overview (one team at a time). This is the thing a flat snapshot can't
    show: whether coaching is actually moving the needle over time."""
    conditions = ["ps.scoring_method = 'heuristic'", "p.is_scorable = true", "p.submitted_at >= now() - (%s || ' days')::interval"]
    params: list = [days]
    if team_id is not None:
        conditions.append("u.team_id = %s")
        params.append(team_id)

    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            SELECT
              date_trunc('day', p.submitted_at)::date::text AS day,
              AVG(ps.composite_score) AS avg_composite,
              AVG(ps.goal_score) AS avg_goal,
              AVG(ps.context_score) AS avg_context,
              AVG(ps.constraints_score) AS avg_constraints,
              AVG(ps.format_score) AS avg_format,
              count(*) AS prompt_count
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            JOIN users u ON u.id = p.user_id
            WHERE {" AND ".join(conditions)}
            GROUP BY day
            ORDER BY day ASC
            """,
            tuple(params),
        )
        rows = await cur.fetchall()

    return schemas.TrendResponse(
        scope=f"team:{team_id}" if team_id else "org",
        points=[
            schemas.TrendPoint(
                day=r["day"],
                avg_composite=round(float(r["avg_composite"]), 2),
                avg_goal=round(float(r["avg_goal"]), 2),
                avg_context=round(float(r["avg_context"]), 2),
                avg_constraints=round(float(r["avg_constraints"]), 2),
                avg_format=round(float(r["avg_format"]), 2),
                prompt_count=r["prompt_count"],
            )
            for r in rows
        ],
    )
