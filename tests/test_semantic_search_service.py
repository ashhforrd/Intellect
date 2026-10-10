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
    project_id = uuid4()
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
        project_id=project_id,
        document_id=document_id,
    )

    assert results == expected_results
    embedding_provider.embed_texts.assert_called_once_with(["dynamic programming"])
    repository.semantic_search.assert_awaited_once_with(
        owner_id="user-123",
        project_id=project_id,
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
            project_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_project_search_boosts_document_name_matches() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    embedding_provider = Mock(spec=EmbeddingProvider)
    feedback_document_id = uuid4()
    proposal_document_id = uuid4()
    project_id = uuid4()
    candidates = [
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=proposal_document_id,
            document_name="Project Proposal.pdf",
            text="A generally relevant proposal section",
            page_number=page,
            score=score,
        )
        for page, score in enumerate((0.91, 0.89, 0.87, 0.85), start=1)
    ]
    candidates.append(
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=feedback_document_id,
            document_name="Feedback Juri.pdf",
            text="Komentar dewan juri dan revisi yang harus dilakukan",
            page_number=1,
            score=0.70,
        )
    )
    embedding_provider.embed_texts.return_value = [[0.1, 0.2]]
    repository.semantic_search.return_value = candidates
    service = SemanticSearchService(repository, embedding_provider)

    results = await service.search(
        query="Apa saja feedback juri yang perlu dikerjakan?",
        owner_id="user-123",
        project_id=project_id,
        limit=5,
    )

    assert results[0].document_id == feedback_document_id
    assert results[0].score == pytest.approx(0.94)
    repository.semantic_search.assert_awaited_once_with(
        owner_id="user-123",
        project_id=project_id,
        query_embedding=[0.1, 0.2],
        limit=20,
        document_id=None,
    )


@pytest.mark.asyncio
async def test_project_search_keeps_multiple_documents_in_final_context() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    embedding_provider = Mock(spec=EmbeddingProvider)
    proposal_document_id = uuid4()
    feedback_document_id = uuid4()
    guide_document_id = uuid4()
    candidates = [
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=proposal_document_id,
            document_name="Proposal.pdf",
            text=f"Proposal section {index}",
            page_number=index,
            score=0.95 - index * 0.01,
        )
        for index in range(6)
    ]
    candidates.extend(
        [
            SemanticSearchResult(
                chunk_id=uuid4(),
                document_id=feedback_document_id,
                document_name="Feedback.pdf",
                text="Jury feedback",
                page_number=1,
                score=0.72,
            ),
            SemanticSearchResult(
                chunk_id=uuid4(),
                document_id=guide_document_id,
                document_name="Guide.pdf",
                text="Final submission guide",
                page_number=1,
                score=0.71,
            ),
        ]
    )
    embedding_provider.embed_texts.return_value = [[0.1, 0.2]]
    repository.semantic_search.return_value = candidates
    service = SemanticSearchService(repository, embedding_provider)

    results = await service.search(
        query="How should the final submission be improved?",
        owner_id="user-123",
        project_id=uuid4(),
        limit=5,
    )

    assert feedback_document_id in {item.document_id for item in results}
    assert guide_document_id in {item.document_id for item in results}
    assert sum(item.document_id == proposal_document_id for item in results) == 3
