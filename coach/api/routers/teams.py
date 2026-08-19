from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException
from psycopg.rows import dict_row

import db
import schemas
from services.progress import compute_progress

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


@router.get("/teams/{team_id}/progress", response_model=schemas.ProgressResponse)
async def get_team_progress(team_id: str) -> schemas.ProgressResponse:
    """Is this team actually getting better, dimension by dimension --
    the team-scoped twin of GET /users/{id}/progress. Recent window is the
    team's most recent 15 scored prompts pooled across all members, which
    skews toward whoever's most active -- a reasonable v1 approximation,
    not a per-member-weighted average."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT name FROM teams WHERE id = %s", (team_id,))
        row = await cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="team not found")
        name = row["name"]

        result = await compute_progress(
            conn, "WHERE u.team_id = %s", (team_id,), scope=f"team:{team_id}", scope_label=name
        )

    return schemas.ProgressResponse(
        scope=result["scope"],
        scope_label=result["scope_label"],
        dimensions=[schemas.DimensionProgress(**dataclasses.asdict(d)) for d in result["dimensions"]],
        strongest_dimension=result["strongest_dimension"],
        weakest_dimension=result["weakest_dimension"],
        headline=result["headline"],
    )
