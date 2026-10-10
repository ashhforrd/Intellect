from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    project_id: UUID
    thread_id: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1, max_length=2000)
    document_id: UUID | None = None
    retrieval_limit: int = Field(default=5, ge=1, le=20)


class QuestionSourceResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    page_number: int | None
    score: float


class PromptAuthorResponse(BaseModel):
    id: UUID
    email: str
    display_name: str


class QuestionResponse(BaseModel):
    answer: str
    sources: list[QuestionSourceResponse]
    author: PromptAuthorResponse


class ConversationTurnResponse(BaseModel):
    id: UUID
    project_id: UUID
    thread_id: str
    question: str
    answer: str
    created_at: datetime
    author: PromptAuthorResponse


class ConversationThreadCreate(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    title: str = Field(default="New conversation", min_length=1, max_length=120)


class ConversationThreadUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    is_archived: bool | None = None


class ConversationThreadResponse(BaseModel):
    id: str
    project_id: UUID
    title: str
    created_by: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
