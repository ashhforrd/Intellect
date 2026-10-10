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
from personal_document_intelligence_api.documents.deletion_service import (
    DocumentDeletionService,
)
from personal_document_intelligence_api.documents.models import (
    ValidatedDocumentUpload,
)
from personal_document_intelligence_api.documents.upload_service import (
    DocumentUploadService,
)
from personal_document_intelligence_api.storage import FileStorage, StorageError


def create_validated_document_upload() -> ValidatedDocumentUpload:
    return ValidatedDocumentUpload(
        filename="document.pdf",
        file_type="pdf",
        size_bytes=100,
    )


def create_database_document() -> Document:
    return Document(
        id=uuid4(),
        owner_id="user-123",
        project_id=uuid4(),
        filename="document.pdf",
        file_type="pdf",
        storage_key="documents/123/document.pdf",
        size_bytes=100,
        page_count=1,
        status=DocumentStatus.UPLOADED,
    )


@pytest.mark.asyncio
async def test_upload_commits_database_transaction() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    storage = Mock(spec=FileStorage)
    database_document = create_database_document()

    repository.create.return_value = database_document

    service = DocumentUploadService(
        session=session,
        repository=repository,
        storage=storage,
    )

    result = await service.upload(
        owner_id="user-123",
        project_id=database_document.project_id,
        file_bytes=b"document content",
        document_upload=create_validated_document_upload(),
    )

    assert result is database_document
    storage.save.assert_called_once()
    repository.create.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_removes_file_when_database_fails() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    storage = Mock(spec=FileStorage)

    repository.create.side_effect = RuntimeError("database unavailable")

    service = DocumentUploadService(
        session=session,
        repository=repository,
        storage=storage,
    )

    with pytest.raises(RuntimeError):
        await service.upload(
            owner_id="user-123",
            project_id=uuid4(),
            file_bytes=b"document content",
            document_upload=create_validated_document_upload(),
        )

    saved_key = storage.save.call_args.args[0]

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
    storage.delete.assert_called_once_with(saved_key)


@pytest.mark.asyncio
async def test_delete_commits_database_transaction() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    storage = Mock(spec=FileStorage)
    document = create_database_document()

    repository.get_by_id.return_value = document

    service = DocumentDeletionService(
        session=session,
        repository=repository,
        storage=storage,
    )

    result = await service.delete(
        document_id=document.id,
        owner_id=document.owner_id,
        project_id=document.project_id,
    )

    assert result is True
    storage.delete.assert_called_once_with(document.storage_key)
    repository.delete.assert_awaited_once_with(document)
    storage.read.assert_not_called()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_does_not_touch_storage_when_database_fails() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    storage = Mock(spec=FileStorage)
    document = create_database_document()

    repository.get_by_id.return_value = document
    repository.delete.side_effect = RuntimeError("database unavailable")

    service = DocumentDeletionService(
        session=session,
        repository=repository,
        storage=storage,
    )

    with pytest.raises(RuntimeError):
        await service.delete(
            document_id=document.id,
            owner_id=document.owner_id,
            project_id=document.project_id,
        )

    session.rollback.assert_awaited_once()
    storage.delete.assert_not_called()
    storage.read.assert_not_called()
    storage.save.assert_not_called()


@pytest.mark.asyncio
async def test_delete_rolls_back_database_when_storage_fails() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DocumentRepository)
    storage = Mock(spec=FileStorage)
    document = create_database_document()

    repository.get_by_id.return_value = document
    storage.delete.side_effect = StorageError("storage unavailable")
    service = DocumentDeletionService(
        session=session,
        repository=repository,
        storage=storage,
    )

    with pytest.raises(StorageError):
        await service.delete(
            document_id=document.id,
            owner_id=document.owner_id,
            project_id=document.project_id,
        )

    repository.delete.assert_awaited_once_with(document)
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
