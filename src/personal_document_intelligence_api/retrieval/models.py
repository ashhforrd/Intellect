from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TextChunk:
    text: str
    section_position: int
    chunk_index: int
    page_number: int | None


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    chunk_id: UUID
    document_id: UUID
    text: str
    page_number: int | None
    score: float
