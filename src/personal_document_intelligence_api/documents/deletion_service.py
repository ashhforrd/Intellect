import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.storage import (
    FileStorage,
    StoredFileNotFoundError,
)


class DocumentDeletionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DocumentRepository,
        storage: FileStorage,
    ) -> None:
        self._session = session
        self._repository = repository
        self._storage = storage

    async def delete(
        self,
        *,
        document_id: UUID,
        owner_id: str,
    ) -> bool:
        document = await self._repository.get_by_id(
            document_id=document_id,
            owner_id=owner_id,
        )

        if document is None:
            return False

        try:
            stored_file = await asyncio.to_thread(
                self._storage.read,
                document.storage_key,
            )
        except StoredFileNotFoundError:
            stored_file = None

        file_deleted = False

        try:
            await asyncio.to_thread(
                self._storage.delete,
                document.storage_key,
            )
            file_deleted = True

            await self._repository.delete(
                document_id=document_id,
                owner_id=owner_id,
            )
            await self._session.commit()

            return True

        except Exception:
            await self._session.rollback()

            if file_deleted and stored_file is not None:
                await asyncio.to_thread(
                    self._storage.save,
                    document.storage_key,
                    stored_file,
                )

            raise
