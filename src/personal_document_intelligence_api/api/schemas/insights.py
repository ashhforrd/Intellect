from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from personal_document_intelligence_api.api.schemas.knowledge import ConversationTurnRequest


class ConversationInsightRequest(BaseModel):
    project_id: UUID
    thread_id: str = Field(min_length=1, max_length=160)
    turns: list[ConversationTurnRequest] = Field(min_length=1, max_length=30)


class InsightTakeawayResponse(BaseModel):
    title: str
    explanation: str
    source_turn_numbers: list[int]


class InsightActionResponse(BaseModel):
    rank: int
    title: str
    rationale: str
    priority: Literal["high", "medium", "low"]
    kind: Literal["explicit", "recommendation", "open_question"]
    source_turn_numbers: list[int]


class ConversationInsightResponse(BaseModel):
    id: UUID
    project_id: UUID
    thread_id: str
    takeaways: list[InsightTakeawayResponse]
    actions: list[InsightActionResponse]
    created_at: datetime
