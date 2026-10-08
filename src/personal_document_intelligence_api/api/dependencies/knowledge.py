from functools import lru_cache

from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.factory import (
    create_knowledge_graph_extractor,
)


@lru_cache
def get_knowledge_graph_extractor() -> KnowledgeGraphExtractor:
    return create_knowledge_graph_extractor()
