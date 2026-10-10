from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document_chunk import (
    DocumentChunk,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.knowledge_graph import (
    KnowledgeGraphRepository,
)
from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
)
from personal_document_intelligence_api.knowledge.service import (
    DocumentHasNoChunksError,
    KnowledgeGraphService,
)


@pytest.mark.asyncio
async def test_generate_knowledge_graph_from_document_chunks() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    extractor = Mock(spec=KnowledgeGraphExtractor)
    document_id = uuid4()
    project_id = uuid4()
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document_id,
        project_id=project_id,
        position=0,
        section_position=0,
        chunk_index=0,
        text="Dynamic programming uses states.",
        page_number=1,
        embedding=[0.1, 0.2],
    )
    expected_graph = KnowledgeGraph(
        concepts=(),
        relations=(),
    )

    repository.list_for_document.return_value = [chunk]
    extractor.extract.return_value = expected_graph
    session = AsyncMock(spec=AsyncSession)
    graph_repository = AsyncMock(spec=KnowledgeGraphRepository)

    service = KnowledgeGraphService(
        session=session,
        repository=repository,
        graph_repository=graph_repository,
        extractor=extractor,
        max_chunks=30,
    )

    graph = await service.generate(
        document_id=document_id,
        owner_id="user-123",
        project_id=project_id,
    )

    assert graph is expected_graph
    repository.list_for_document.assert_awaited_once_with(
        document_id=document_id,
        owner_id="user-123",
        project_id=project_id,
        limit=30,
    )

    graph_repository.replace_for_document.assert_awaited_once_with(
        document_id,
        expected_graph,
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_document_without_chunks() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    extractor = Mock(spec=KnowledgeGraphExtractor)
    repository.list_for_document.return_value = []
    session = AsyncMock(spec=AsyncSession)
    graph_repository = AsyncMock(spec=KnowledgeGraphRepository)

    service = KnowledgeGraphService(
        session=session,
        repository=repository,
        graph_repository=graph_repository,
        extractor=extractor,
        max_chunks=30,
    )

    with pytest.raises(DocumentHasNoChunksError):
        await service.generate(
            document_id=uuid4(),
            owner_id="user-123",
            project_id=uuid4(),
        )

    extractor.extract.assert_not_called()
    graph_repository.replace_for_document.assert_not_awaited()
    session.commit.assert_not_awaited()
