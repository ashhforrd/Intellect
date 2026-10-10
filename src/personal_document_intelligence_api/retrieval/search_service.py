import asyncio
from uuid import UUID

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
    EmbeddingProviderError,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


class EmptySearchQueryError(ValueError):
    pass


class SemanticSearchService:
    def __init__(
        self,
        repository: DocumentChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider

    async def search(
        self,
        *,
        query: str,
        owner_id: str,
        project_id: UUID,
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[SemanticSearchResult]:
        normalized_query = " ".join(query.split())

        if not normalized_query:
            raise EmptySearchQueryError("Search query must not be empty")

        embeddings = await asyncio.to_thread(
            self.embedding_provider.embed_texts,
            [normalized_query],
        )

        if len(embeddings) != 1:
            raise EmbeddingProviderError("Embedding provider returned an unexpected result")

        return await self.repository.semantic_search(
            owner_id=owner_id,
            project_id=project_id,
            query_embedding=embeddings[0],
            limit=limit,
            document_id=document_id,
        )
