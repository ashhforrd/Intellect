import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import Document
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.documents.models import (
    ValidatedDocumentUpload,
)
from personal_document_intelligence_api.storage import FileStorage


class DocumentUploadService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DocumentRepository,
        storage: FileStorage,
    ) -> None:
        self._session = session
        self._repository = repository
        self._storage = storage

    async def upload(
        self,
        *,
        owner_id: str,
        project_id: UUID,
        file_bytes: bytes,
        document_upload: ValidatedDocumentUpload,
    ) -> Document:
        storage_key = self._create_storage_key(document_upload.filename)
        file_saved = False

        try:
            await asyncio.to_thread(
                self._storage.save,
                storage_key,
                file_bytes,
            )
            file_saved = True

            document = await self._repository.create(
                owner_id=owner_id,
                project_id=project_id,
                filename=document_upload.filename,
                file_type=document_upload.file_type,
                storage_key=storage_key,
                size_bytes=document_upload.size_bytes,
                page_count=None,
            )

            await self._session.commit()

            return document

        except Exception:
            await self._session.rollback()

            if file_saved:
                await asyncio.to_thread(
                    self._storage.delete,
                    storage_key,
                )

            raise

    @staticmethod
    def _create_storage_key(filename: str) -> str:
        document_id = uuid4()

        return f"documents/{document_id}/{filename}"
