from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeConceptResponse(BaseModel):
    id: str
    label: str
    description: str
    source_chunk_ids: list[UUID]


class KnowledgeRelationResponse(BaseModel):
    source_id: str
    target_id: str
    label: str
    source_chunk_ids: list[UUID]


class KnowledgeGraphResponse(BaseModel):
    concepts: list[KnowledgeConceptResponse]
    relations: list[KnowledgeRelationResponse]


class ConversationTurnRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1, max_length=12000)


class ConversationGraphRequest(BaseModel):
    turns: list[ConversationTurnRequest] = Field(min_length=1, max_length=20)
