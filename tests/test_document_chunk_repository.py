from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document_chunk import (
    DocumentChunk,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    ChunkEmbeddingCountMismatchError,
    DocumentChunkRepository,
)
from personal_document_intelligence_api.retrieval.models import TextChunk


@pytest.mark.asyncio
async def test_replace_document_chunks() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = DocumentChunkRepository(session)
    document_id = uuid4()
    project_id = uuid4()
    chunks = [
        TextChunk(
            text="First chunk",
            section_position=0,
            chunk_index=0,
            page_number=1,
        )
    ]

    await repository.replace_for_document(
        document_id=document_id,
        project_id=project_id,
        chunks=chunks,
        embeddings=[[0.1, 0.2]],
    )

    stored_chunks = session.add_all.call_args.args[0]

    assert len(stored_chunks) == 1
    assert stored_chunks[0].document_id == document_id
    assert stored_chunks[0].project_id == project_id
    assert stored_chunks[0].text == "First chunk"
    assert list(stored_chunks[0].embedding) == [0.1, 0.2]
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_mismatched_chunk_and_embedding_counts() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = DocumentChunkRepository(session)

    with pytest.raises(ChunkEmbeddingCountMismatchError):
        await repository.replace_for_document(
            document_id=uuid4(),
            project_id=uuid4(),
            chunks=[
                TextChunk(
                    text="Chunk",
                    section_position=0,
                    chunk_index=0,
                    page_number=1,
                )
            ],
            embeddings=[],
        )


@pytest.mark.asyncio
async def test_semantic_search_maps_distance_to_similarity() -> None:
    session = AsyncMock(spec=AsyncSession)
    query_result = Mock()
    document_id = uuid4()
    project_id = uuid4()

    stored_chunk = DocumentChunk(
        id=uuid4(),
        document_id=document_id,
        project_id=project_id,
        position=0,
        section_position=0,
        chunk_index=0,
        text="Relevant document content",
        page_number=1,
        embedding=[0.1, 0.2],
    )

    query_result.all.return_value = [(stored_chunk, 0.15)]
    session.execute.return_value = query_result

    repository = DocumentChunkRepository(session)

    results = await repository.semantic_search(
        owner_id="user-123",
        project_id=project_id,
        query_embedding=[0.1, 0.2],
        limit=5,
    )

    assert len(results) == 1
    assert results[0].text == "Relevant document content"
    assert results[0].score == pytest.approx(0.85)
