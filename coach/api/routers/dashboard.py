from __future__ import annotations

from fastapi import APIRouter
from psycopg.rows import dict_row

import db

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
