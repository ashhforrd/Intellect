from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from personal_document_intelligence_api.database.models.document_chunk import (
    DocumentChunk,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
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
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document_id,
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

    service = KnowledgeGraphService(
        repository=repository,
        extractor=extractor,
        max_chunks=30,
    )

    graph = await service.generate(
        document_id=document_id,
        owner_id="user-123",
    )

    assert graph is expected_graph
    repository.list_for_document.assert_awaited_once_with(
        document_id=document_id,
        owner_id="user-123",
        limit=30,
    )


@pytest.mark.asyncio
async def test_reject_document_without_chunks() -> None:
    repository = AsyncMock(spec=DocumentChunkRepository)
    extractor = Mock(spec=KnowledgeGraphExtractor)
    repository.list_for_document.return_value = []

    service = KnowledgeGraphService(
        repository=repository,
        extractor=extractor,
        max_chunks=30,
    )

    with pytest.raises(DocumentHasNoChunksError):
        await service.generate(
            document_id=uuid4(),
            owner_id="user-123",
        )

    extractor.extract.assert_not_called()
