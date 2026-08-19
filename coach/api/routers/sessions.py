from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from psycopg.rows import dict_row

import db
import schemas
from auth import require_token
from services.coaching import compose_end_of_session_summary
from services.identity import get_or_create_session, get_or_create_user
from services.level_engine import compute_session_level

router = APIRouter()


@router.post(
    "/sessions/end",
    response_model=schemas.SessionEndResponse,
    dependencies=[Depends(require_token)],
)
async def end_session(body: schemas.SessionEndRequest) -> schemas.SessionEndResponse:
    """Called from coach/hooks/lib/end_session_worker.py (detached from the
    SessionEnd hook's own tiny timeout budget) and from the stale-session
    sweep in main.py for sessions whose hook never fired."""
    async with db.pool.connection() as conn:
        user_id = await get_or_create_user(conn, body.user_email, None)
        session_id = await get_or_create_session(conn, user_id, body.claude_session_id)

        session_level = await compute_session_level(conn, session_id)

        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE sessions SET ended_at = now(), session_level = %s "
                "WHERE id = %s AND ended_at IS NULL",
                (session_level, session_id),
            )

            await cur.execute("SELECT coaching_mode FROM users WHERE id = %s", (user_id,))
            (coaching_mode,) = await cur.fetchone()

        feedback_queued = False
        if coaching_mode == "end_of_session":
            summary = await compose_end_of_session_summary(conn, user_id, session_id)
            if summary:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO coaching_feedback
                            (session_id, user_id, feedback_type, feedback_text)
                        VALUES (%s, %s, 'end_of_session', %s)
                        """,
                        (session_id, user_id, summary),
                    )
                feedback_queued = True

    return schemas.SessionEndResponse(
        session_id=session_id, session_level=session_level, feedback_queued=feedback_queued
    )


@router.get(
    "/users/{email}/undelivered-feedback",
    response_model=schemas.UndeliveredFeedbackResponse,
)
async def undelivered_feedback(email: str) -> schemas.UndeliveredFeedbackResponse:
    """Polled by coach/hooks/on_session_start.py so an end_of_session summary
    reaches the user at the START of their next session (SessionEnd's own
    timeout is too tight to deliver anything itself -- see coach/README.md)."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT cf.id, cf.feedback_text, cf.created_at
            FROM coaching_feedback cf
            JOIN users u ON u.id = cf.user_id
            WHERE u.email = %s AND cf.delivered_at IS NULL
            ORDER BY cf.created_at ASC
            """,
            (email,),
        )
        rows = await cur.fetchall()

        if rows:
            ids = [r["id"] for r in rows]
            await cur.execute(
                "UPDATE coaching_feedback SET delivered_at = now() WHERE id = ANY(%s)",
                (ids,),
            )

    return schemas.UndeliveredFeedbackResponse(
        items=[schemas.UndeliveredFeedback(**row) for row in rows]
    )


@router.get("/sessions/{session_id}", response_model=schemas.SessionDetail)
async def get_session_detail(session_id: str) -> schemas.SessionDetail:
    """The session drill-down: every prompt in it, each with its full
    per-dimension breakdown -- the level between one prompt and a user's
    whole history."""
    async with db.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
              s.id, s.claude_session_id, s.started_at, s.ended_at,
              s.session_level, l.name AS session_level_name,
              count(p.id) FILTER (WHERE p.is_scorable) AS prompt_count,
              AVG(ps.composite_score) AS avg_composite
            FROM sessions s
            LEFT JOIN levels l ON l.level_num = s.session_level
            LEFT JOIN prompts p ON p.session_id = s.id
            LEFT JOIN prompt_scores ps ON ps.prompt_id = p.id AND ps.scoring_method = 'heuristic'
            WHERE s.id = %s
            GROUP BY s.id, s.claude_session_id, s.started_at, s.ended_at, s.session_level, l.name
            """,
            (session_id,),
        )
        session_row = await cur.fetchone()
        if session_row is None:
            raise HTTPException(status_code=404, detail="session not found")
        session_row = {
            **session_row,
            "avg_composite": round(float(session_row["avg_composite"]), 2)
            if session_row["avg_composite"] is not None
            else None,
        }

        await cur.execute(
            "SELECT id, prompt_text, is_scorable, submitted_at FROM prompts "
            "WHERE session_id = %s ORDER BY submitted_at ASC",
            (session_id,),
        )
        prompt_rows = await cur.fetchall()

        scores_by_prompt: dict = {}
        if prompt_rows:
            prompt_ids = [r["id"] for r in prompt_rows]
            await cur.execute(
                """
                SELECT prompt_id, scoring_method, goal_score, context_score,
                       constraints_score, format_score, composite_score, rationale,
                       dimension_feedback, latency_ms
                FROM prompt_scores WHERE prompt_id = ANY(%s)
                """,
                (prompt_ids,),
            )
            for s in await cur.fetchall():
                scores_by_prompt.setdefault(s["prompt_id"], []).append(
                    schemas.PromptScoreOut(**{k: v for k, v in s.items() if k != "prompt_id"})
                )

    return schemas.SessionDetail(
        session=schemas.SessionSummary(**session_row),
        prompts=[
            schemas.PromptOut(
                id=r["id"], prompt_text=r["prompt_text"], is_scorable=r["is_scorable"],
                submitted_at=r["submitted_at"], scores=scores_by_prompt.get(r["id"], []),
            )
            for r in prompt_rows
        ],
    )
