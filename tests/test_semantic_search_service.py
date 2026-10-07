from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)
from personal_document_intelligence_api.retrieval.search_service import (
    EmptySearchQueryError,
    SemanticSearchService,
)


@pytest.mark.asyncio
async def test_semantic_search_embeds_query_and_searches_repository() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    embedding_provider = Mock(spec=EmbeddingProvider)
    document_id = uuid4()
    expected_results = [
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=document_id,
            text="Dynamic programming stores repeated subproblem results.",
            page_number=1,
            score=0.91,
        )
    ]

    embedding_provider.embed_texts.return_value = [[0.1, 0.2]]
    repository.semantic_search.return_value = expected_results

    service = SemanticSearchService(
        repository=repository,
        embedding_provider=embedding_provider,
    )

    results = await service.search(
        query="  dynamic   programming  ",
        owner_id="user-123",
        document_id=document_id,
    )

    assert results == expected_results
    embedding_provider.embed_texts.assert_called_once_with(["dynamic programming"])
    repository.semantic_search.assert_awaited_once_with(
        owner_id="user-123",
        query_embedding=[0.1, 0.2],
        limit=5,
        document_id=document_id,
    )


@pytest.mark.asyncio
async def test_semantic_search_rejects_empty_query() -> None:
    service = SemanticSearchService(
        repository=AsyncMock(spec=DocumentChunkRepository),
        embedding_provider=Mock(spec=EmbeddingProvider),
    )

    with pytest.raises(EmptySearchQueryError):
        await service.search(
            query="   ",
            owner_id="user-123",
        )
