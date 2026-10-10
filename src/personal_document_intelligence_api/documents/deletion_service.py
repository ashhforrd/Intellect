import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.storage import (
    FileStorage,
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
        project_id: UUID,
    ) -> bool:
        document = await self._repository.get_by_id(
            document_id=document_id,
            owner_id=owner_id,
            project_id=project_id,
        )

        if document is None:
            return False

        try:
            # Flush the relational delete first. If storage deletion fails, the
            # transaction can still be rolled back without downloading a copy
            # of the original object from S3.
            await self._repository.delete(document)

            await asyncio.to_thread(
                self._storage.delete,
                document.storage_key,
            )
            await self._session.commit()

            return True

        except Exception:
            await self._session.rollback()
            raise
