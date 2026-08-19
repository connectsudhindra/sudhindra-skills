from __future__ import annotations

from fastapi import APIRouter
from psycopg.rows import dict_row

import db
import schemas

router = APIRouter()


@router.get("/teams", response_model=list[schemas.TeamOut])
async def list_teams() -> list[schemas.TeamOut]:
    """Backs the Teams overview -- every team, cross-team comparison at a
    glance (member count, average level, average rolling composite)."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
              t.id, t.name,
              count(u.id) AS member_count,
              AVG(u.current_level) AS avg_level,
              (
                SELECT AVG(ps.composite_score)
                FROM prompt_scores ps
                JOIN prompts p ON p.id = ps.prompt_id
                JOIN users u2 ON u2.id = p.user_id
                WHERE u2.team_id = t.id AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
              ) AS avg_composite
            FROM teams t
            LEFT JOIN users u ON u.team_id = t.id
            GROUP BY t.id, t.name
            ORDER BY avg_composite DESC NULLS LAST
            """
        )
        rows = await cur.fetchall()

    return [
        schemas.TeamOut(
            id=r["id"],
            name=r["name"],
            member_count=r["member_count"],
            avg_level=round(float(r["avg_level"]), 2) if r["avg_level"] is not None else None,
            avg_composite=round(float(r["avg_composite"]), 2) if r["avg_composite"] is not None else None,
        )
        for r in rows
    ]
