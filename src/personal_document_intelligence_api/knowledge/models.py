from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class KnowledgeConcept:
    id: str
    label: str
    description: str
    source_chunk_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    source_id: str
    target_id: str
    label: str
    source_chunk_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeGraph:
    concepts: tuple[KnowledgeConcept, ...]
    relations: tuple[KnowledgeRelation, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    chunk_id: UUID
    text: str
