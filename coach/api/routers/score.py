from __future__ import annotations

from fastapi import APIRouter, Depends

import schemas
from auth import require_token
from scoring import heuristic, llm

router = APIRouter()


@router.post("/score", response_model=schemas.ScoreResponse, dependencies=[Depends(require_token)])
async def score_prompt(body: schemas.ScoreRequest) -> schemas.ScoreResponse:
    """Score a prompt without persisting anything -- no prompts/prompt_scores
    row, no effect on leveling. For "check this before I send it" use cases
    (the MCP server's `score_prompt` tool is the main caller) where a
    dry-run matters more than a permanent record. `POST /prompts` remains
    the only way to actually persist a score and affect a user's level."""
    heuristic_score = heuristic.score_prompt(body.prompt_text)

    llm_score = None
    llm_error = None
    if body.include_llm:
        try:
            scores, _latency_ms = await llm.score_prompt(body.prompt_text)
            llm_score = schemas.GCCFScore(
                goal=scores["goal"], context=scores["context"], constraints=scores["constraints"],
                format=scores["format"], rationale=scores.get("rationale"),
            )
        except llm.LLMScoringError as exc:
            llm_error = str(exc)

    return schemas.ScoreResponse(
        heuristic=schemas.GCCFScore(
            goal=heuristic_score.goal, context=heuristic_score.context,
            constraints=heuristic_score.constraints, format=heuristic_score.format,
            rationale=heuristic_score.rationale, dimensions=heuristic_score.dimensions_json(),
        ),
        llm=llm_score,
        llm_error=llm_error,
    )
