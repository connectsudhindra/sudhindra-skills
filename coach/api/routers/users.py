from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

import db
import schemas

router = APIRouter()

_USER_SUMMARY_SQL = """
SELECT
  u.id, u.name, u.email, u.current_level, l.name AS current_level_name,
  u.coaching_mode,
  (
    SELECT AVG(ps.composite_score)
    FROM (
      SELECT ps.composite_score
      FROM prompt_scores ps
      JOIN prompts p ON p.id = ps.prompt_id
      WHERE p.user_id = u.id AND p.is_scorable = true AND ps.scoring_method = 'heuristic'
      ORDER BY p.submitted_at DESC
      LIMIT 20
    ) ps
  ) AS rolling_composite,
  (SELECT count(*) FROM prompts p WHERE p.user_id = u.id AND p.is_scorable = true) AS scorable_prompt_count,
  (SELECT max(p.submitted_at) FROM prompts p WHERE p.user_id = u.id) AS last_active
FROM users u
JOIN levels l ON l.level_num = u.current_level
"""


def _resolve_user_id_or_404(row) -> None:
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")


@router.get("/users", response_model=list[schemas.UserSummary])
async def list_users(level: int | None = Query(default=None)) -> list[schemas.UserSummary]:
    """Backs the Team Roster screen -- every installed user, optionally
    filtered to one level."""
    sql = _USER_SUMMARY_SQL
    params: tuple = ()
    if level is not None:
        sql += " WHERE u.current_level = %s"
        params = (level,)
    sql += " ORDER BY u.current_level DESC, rolling_composite DESC NULLS LAST"

    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()
    return [schemas.UserSummary(**row) for row in rows]


@router.get("/users/by-email/{email}", response_model=schemas.UserSummary)
async def get_user_by_email(email: str) -> schemas.UserSummary:
    """Backs the 'My Coaching' screen -- resolves a user from their own
    locally-configured email, no admin controls exposed on that path."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(_USER_SUMMARY_SQL + " WHERE u.email = %s", (email,))
        row = await cur.fetchone()
    _resolve_user_id_or_404(row)
    return schemas.UserSummary(**row)


@router.get("/users/{user_id}", response_model=schemas.UserDetail)
async def get_user_detail(user_id: str) -> schemas.UserDetail:
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(_USER_SUMMARY_SQL + " WHERE u.id = %s", (user_id,))
        user_row = await cur.fetchone()
        _resolve_user_id_or_404(user_row)

        await cur.execute(
            "SELECT level_num, achieved_at FROM level_history "
            "WHERE user_id = %s ORDER BY achieved_at ASC",
            (user_id,),
        )
        history = await cur.fetchall()

        await cur.execute(
            """
            SELECT AVG(goal_score) AS goal, AVG(context_score) AS context,
                   AVG(constraints_score) AS constraints, AVG(format_score) AS format
            FROM prompt_scores ps
            JOIN prompts p ON p.id = ps.prompt_id
            WHERE p.user_id = %s AND ps.scoring_method = 'heuristic' AND p.is_scorable = true
            """,
            (user_id,),
        )
        avg_row = await cur.fetchone()

    gccf_averages = None
    if avg_row and avg_row["goal"] is not None:
        gccf_averages = schemas.GCCFScore(
            goal=round(float(avg_row["goal"]), 2),
            context=round(float(avg_row["context"]), 2),
            constraints=round(float(avg_row["constraints"]), 2),
            format=round(float(avg_row["format"]), 2),
        )

    return schemas.UserDetail(
        user=schemas.UserSummary(**user_row),
        level_history=[dict(h) for h in history],
        gccf_averages=gccf_averages,
    )


@router.get("/users/{user_id}/prompts", response_model=list[schemas.PromptOut])
async def get_user_prompts(
    user_id: str, limit: int = Query(default=50, le=200), offset: int = Query(default=0)
) -> list[schemas.PromptOut]:
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, prompt_text, is_scorable, submitted_at
            FROM prompts WHERE user_id = %s
            ORDER BY submitted_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        prompt_rows = await cur.fetchall()
        if not prompt_rows:
            return []

        prompt_ids = [r["id"] for r in prompt_rows]
        await cur.execute(
            """
            SELECT prompt_id, scoring_method, goal_score, context_score,
                   constraints_score, format_score, composite_score, rationale, latency_ms
            FROM prompt_scores WHERE prompt_id = ANY(%s)
            """,
            (prompt_ids,),
        )
        score_rows = await cur.fetchall()

    scores_by_prompt: dict = {}
    for s in score_rows:
        scores_by_prompt.setdefault(s["prompt_id"], []).append(
            schemas.PromptScoreOut(**{k: v for k, v in s.items() if k != "prompt_id"})
        )

    return [
        schemas.PromptOut(
            id=r["id"],
            prompt_text=r["prompt_text"],
            is_scorable=r["is_scorable"],
            submitted_at=r["submitted_at"],
            scores=scores_by_prompt.get(r["id"], []),
        )
        for r in prompt_rows
    ]


@router.get("/users/{user_id}/feedback")
async def get_user_feedback(user_id: str, limit: int = Query(default=20, le=100)) -> list[dict]:
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, feedback_type, feedback_text, blocked, delivered_at, created_at
            FROM coaching_feedback WHERE user_id = %s
            ORDER BY created_at DESC LIMIT %s
            """,
            (user_id, limit),
        )
        rows = await cur.fetchall()
    return rows
