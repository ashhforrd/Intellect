from uuid import UUID

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_id: UUID | None = None
    retrieval_limit: int = Field(default=5, ge=1, le=20)


class QuestionSourceResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    page_number: int | None
    score: float


class QuestionResponse(BaseModel):
    answer: str
    sources: list[QuestionSourceResponse]
