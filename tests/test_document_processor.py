from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import (
    Document,
    DocumentStatus,
)
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.document_section import (
    DocumentSectionRepository,
)
from personal_document_intelligence_api.documents.models import (
    DocumentSection,
    ExtractionMethod,
    ParsedDocument,
)
from personal_document_intelligence_api.documents.service import (
    DocumentExtractionService,
)
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
)
from personal_document_intelligence_api.storage.base import FileStorage
from personal_document_intelligence_api.workers.document_processor import (
    DocumentProcessor,
)


@pytest.mark.asyncio
async def test_process_document_successfully() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    section_repository = AsyncMock(spec=DocumentSectionRepository)
    storage = Mock(spec=FileStorage)
    extraction_service = Mock(spec=DocumentExtractionService)
    chunk_repository = AsyncMock(spec=DocumentChunkRepository)
    embedding_provider = Mock(spec=EmbeddingProvider)
    embedding_provider.embed_texts.return_value = [[0.1, 0.2]]

    document = Document(
        id=uuid4(),
        owner_id="user-123",
        project_id=uuid4(),
        filename="document.pdf",
        file_type="pdf",
        storage_key="documents/123/document.pdf",
        size_bytes=100,
        status=DocumentStatus.UPLOADED,
    )
    parsed_document = ParsedDocument(
        filename="document.pdf",
        file_type="pdf",
        size_bytes=100,
        page_count=1,
        sections=(
            DocumentSection(
                text="Extracted content",
                page_number=1,
                extraction_method=ExtractionMethod.NATIVE,
            ),
        ),
    )

    repository.get_by_id_internal.return_value = document
    storage.read.return_value = b"document bytes"
    extraction_service.extract.return_value = parsed_document

    processor = DocumentProcessor(
        session=session,
        repository=repository,
        section_repository=section_repository,
        chunk_repository=chunk_repository,
        storage=storage,
        extraction_service=extraction_service,
        embedding_provider=embedding_provider,
    )

    result = await processor.process(document.id)

    assert result is True
    embedding_provider.embed_texts.assert_called_once_with(["Extracted content"])
    chunk_repository.replace_for_document.assert_awaited_once()
    repository.mark_processing.assert_awaited_once_with(document)
    storage.read.assert_called_once_with(document.storage_key)
    section_repository.replace_for_document.assert_awaited_once_with(
        document.id,
        parsed_document.sections,
    )
    repository.mark_ready.assert_awaited_once_with(document, 1)
    assert session.commit.await_count == 2


@pytest.mark.asyncio
async def test_skip_job_when_document_was_already_deleted() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    repository.get_by_id_internal.return_value = None
    processor = DocumentProcessor(
        session=session,
        repository=repository,
        section_repository=AsyncMock(spec=DocumentSectionRepository),
        chunk_repository=AsyncMock(spec=DocumentChunkRepository),
        storage=Mock(spec=FileStorage),
        extraction_service=Mock(spec=DocumentExtractionService),
        embedding_provider=Mock(spec=EmbeddingProvider),
    )

    result = await processor.process(uuid4())

    assert result is False
    repository.mark_processing.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_skip_retry_when_document_is_deleted_during_processing() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    document = Document(
        id=uuid4(),
        owner_id="user-123",
        project_id=uuid4(),
        filename="document.pdf",
        file_type="pdf",
        storage_key="documents/123/document.pdf",
        size_bytes=100,
        status=DocumentStatus.UPLOADED,
    )
    repository.get_by_id_internal.side_effect = [document, None]
    storage = Mock(spec=FileStorage)
    storage.read.side_effect = FileNotFoundError("document was deleted")
    processor = DocumentProcessor(
        session=session,
        repository=repository,
        section_repository=AsyncMock(spec=DocumentSectionRepository),
        chunk_repository=AsyncMock(spec=DocumentChunkRepository),
        storage=storage,
        extraction_service=Mock(spec=DocumentExtractionService),
        embedding_provider=Mock(spec=EmbeddingProvider),
    )

    result = await processor.process(document.id)

    assert result is False
    session.rollback.assert_awaited_once()
    repository.mark_failed.assert_not_awaited()
