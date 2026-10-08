from uuid import UUID

from pydantic import BaseModel


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
