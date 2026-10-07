from dataclasses import dataclass

from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


@dataclass(frozen=True, slots=True)
class RagAnswer:
    answer: str
    sources: tuple[SemanticSearchResult, ...]
