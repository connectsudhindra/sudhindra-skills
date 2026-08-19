"""Pydantic request/response models. Kept flat in one file -- the whole API
surface is small enough that splitting per-router would just add indirection.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CoachingMode = Literal["in_session", "end_of_session", "off"]
ScoringMethod = Literal["heuristic", "llm"]
FeedbackType = Literal["in_session", "end_of_session"]


class GCCFScore(BaseModel):
    goal: float = Field(ge=0, le=100)
    context: float = Field(ge=0, le=100)
    constraints: float = Field(ge=0, le=100)
    format: float = Field(ge=0, le=100)
    rationale: str | None = None

    @property
    def composite(self) -> float:
        return round((self.goal + self.context + self.constraints + self.format) / 4, 2)


class PromptSubmitRequest(BaseModel):
    user_email: str
    user_name: str | None = None
    claude_session_id: str
    prompt_text: str
    is_scorable: bool = True
    request_llm_score: bool = True


class PromptSubmitResponse(BaseModel):
    prompt_id: UUID
    heuristic_score: GCCFScore
    current_level: int
    current_level_name: str
    leveled_up: bool


class SessionEndRequest(BaseModel):
    user_email: str
    claude_session_id: str


class SessionEndResponse(BaseModel):
    session_id: UUID
    session_level: int | None
    feedback_queued: bool


class UndeliveredFeedback(BaseModel):
    id: UUID
    feedback_text: str
    created_at: datetime


class UndeliveredFeedbackResponse(BaseModel):
    items: list[UndeliveredFeedback]


class LevelOut(BaseModel):
    level_num: int
    name: str
    min_score: float
    description: str | None
    next_level_tip: str | None


class PromptScoreOut(BaseModel):
    scoring_method: ScoringMethod
    goal_score: float
    context_score: float
    constraints_score: float
    format_score: float
    composite_score: float
    rationale: str | None
    latency_ms: int | None


class PromptOut(BaseModel):
    id: UUID
    prompt_text: str
    is_scorable: bool
    submitted_at: datetime
    scores: list[PromptScoreOut]


class UserSummary(BaseModel):
    id: UUID
    name: str
    email: str
    team_id: UUID | None
    team_name: str | None
    current_level: int
    current_level_name: str
    coaching_mode: CoachingMode
    rolling_composite: float | None
    scorable_prompt_count: int
    last_active: datetime | None


class UserDetail(BaseModel):
    user: UserSummary
    level_history: list[dict]
    gccf_averages: GCCFScore | None


class TeamOut(BaseModel):
    id: UUID
    name: str
    member_count: int
    avg_level: float | None
    avg_composite: float | None


class TrendPoint(BaseModel):
    day: str
    avg_composite: float
    prompt_count: int


class TrendResponse(BaseModel):
    scope: str
    points: list[TrendPoint]
