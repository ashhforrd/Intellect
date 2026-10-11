from collections.abc import Sequence
from typing import Protocol

from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)

from .options import GenerationOptions


class AnswerGenerationError(Exception):
    pass


class AnswerGenerationIncompleteError(AnswerGenerationError):
    pass


class AnswerGenerator(Protocol):
    def generate(
        self,
        question: str,
        contexts: Sequence[SemanticSearchResult],
        *,
        options: GenerationOptions | None = None,
    ) -> str: ...
