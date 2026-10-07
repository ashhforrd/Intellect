from uuid import UUID

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    document_id: UUID | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SemanticSearchResultResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    page_number: int | None
    score: float
