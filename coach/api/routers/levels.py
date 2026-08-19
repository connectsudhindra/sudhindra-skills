from __future__ import annotations

from fastapi import APIRouter
from psycopg.rows import dict_row

import db
import schemas

router = APIRouter()


@router.get("/levels", response_model=list[schemas.LevelOut])
async def list_levels() -> list[schemas.LevelOut]:
    """The five levels and their thresholds -- static reference data, but
    exposed over the API (rather than left for clients to hardcode) so an
    MCP client can explain "what's next" without a copy of db/seed/seed_levels.sql."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT level_num, name, min_score, description, next_level_tip "
            "FROM levels ORDER BY level_num"
        )
        rows = await cur.fetchall()
    return [schemas.LevelOut(**{**r, "min_score": float(r["min_score"])}) for r in rows]
