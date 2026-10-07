from collections.abc import Sequence
from typing import Protocol

from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


class AnswerGenerationError(Exception):
    pass


class AnswerGenerator(Protocol):
    def generate(
        self,
        question: str,
        contexts: Sequence[SemanticSearchResult],
    ) -> str: ...
