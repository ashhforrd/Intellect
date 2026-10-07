from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
        chunks=chunks,
        embeddings=[[0.1, 0.2]],
    )

    stored_chunks = session.add_all.call_args.args[0]

    assert len(stored_chunks) == 1
    assert stored_chunks[0].document_id == document_id
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
