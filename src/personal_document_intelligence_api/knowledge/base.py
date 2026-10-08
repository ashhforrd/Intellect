from collections.abc import Sequence
from typing import Protocol

from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
    KnowledgeSource,
)


class KnowledgeGraphExtractor(Protocol):
    def extract(
        self,
        contexts: Sequence[KnowledgeSource],
    ) -> KnowledgeGraph: ...
