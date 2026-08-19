from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from psycopg.types.json import Json

import config
import db
import schemas
from auth import require_token
from scoring import heuristic, llm
from services.identity import get_or_create_session, get_or_create_user
from services.level_engine import LevelResult, recompute_user_level

router = APIRouter()
logger = logging.getLogger("coach.prompts")


async def _score_llm_background(prompt_id: str) -> None:
    """Runs after the response has already gone back to the hook. Best-effort:
    any failure here just means no 'llm' row for this prompt -- the heuristic
    row (already committed synchronously) is unaffected."""
    async with db.pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("SELECT prompt_text FROM prompts WHERE id = %s", (prompt_id,))
        row = await cur.fetchone()
        if not row:
            return
        (prompt_text,) = row

        try:
            scores, latency_ms = await llm.score_prompt(prompt_text)
        except llm.LLMScoringError as exc:
            logger.info("llm scoring skipped for %s: %s", prompt_id, exc)
            return

        await cur.execute(
            """
            INSERT INTO prompt_scores
                (prompt_id, scoring_method, model_name, goal_score, context_score,
                 constraints_score, format_score, rationale, latency_ms)
            VALUES (%s, 'llm', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (prompt_id, scoring_method) DO NOTHING
            """,
            (
                prompt_id,
                config.LLM_MODEL,
                scores["goal"],
                scores["context"],
                scores["constraints"],
                scores["format"],
                scores.get("rationale"),
                latency_ms,
            ),
        )


@router.post(
    "/prompts",
    response_model=schemas.PromptSubmitResponse,
    dependencies=[Depends(require_token)],
)
async def submit_prompt(
    body: schemas.PromptSubmitRequest, background_tasks: BackgroundTasks
) -> schemas.PromptSubmitResponse:
    """Called from coach/hooks/on_prompt_submit.py for every prompt (whether or
    not it was already blocked locally by the hook's own heuristic check --
    this endpoint is the single source of truth for persisted scores and
    leveling, independent of what the hook decided)."""
    async with db.pool.connection() as conn:
        user_id = await get_or_create_user(conn, body.user_email, body.user_name)
        session_id = await get_or_create_session(conn, user_id, body.claude_session_id)

        score = heuristic.score_prompt(body.prompt_text)

        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO prompts (session_id, user_id, prompt_text, is_scorable)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (session_id, user_id, body.prompt_text, body.is_scorable),
            )
            (prompt_id,) = await cur.fetchone()

            if body.is_scorable:
                await cur.execute(
                    """
                    INSERT INTO prompt_scores
                        (prompt_id, scoring_method, goal_score, context_score,
                         constraints_score, format_score, rationale, dimension_feedback)
                    VALUES (%s, 'heuristic', %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        prompt_id, score.goal, score.context, score.constraints, score.format,
                        score.rationale, Json(score.dimensions_json()),
                    ),
                )

        if body.is_scorable:
            level_result = await recompute_user_level(conn, user_id)
        else:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT users.current_level, levels.name FROM users "
                    "JOIN levels ON levels.level_num = users.current_level WHERE users.id = %s",
                    (user_id,),
                )
                current_level, level_name = await cur.fetchone()
            level_result = LevelResult(current_level, level_name, None, leveled_up=False)

        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE prompts SET level_at_submission = %s WHERE id = %s",
                (level_result.level_num, prompt_id),
            )

    if body.is_scorable and body.request_llm_score:
        background_tasks.add_task(_score_llm_background, str(prompt_id))

    return schemas.PromptSubmitResponse(
        prompt_id=prompt_id,
        heuristic_score=schemas.GCCFScore(
            goal=score.goal, context=score.context, constraints=score.constraints,
            format=score.format, rationale=score.rationale, dimensions=score.dimensions_json(),
        ),
        current_level=level_result.level_num,
        current_level_name=level_result.level_name,
        leveled_up=level_result.leveled_up,
    )
