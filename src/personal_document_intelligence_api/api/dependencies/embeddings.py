from functools import lru_cache

from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
)
from personal_document_intelligence_api.retrieval.embeddings.factory import (
    create_embedding_provider,
)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return create_embedding_provider()
