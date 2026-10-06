import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import (
    DocumentStatus,
)
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_section import (
    DocumentSectionRepository,
)
from personal_document_intelligence_api.documents.service import (
    DocumentExtractionService,
)
from personal_document_intelligence_api.storage.base import FileStorage


class DocumentProcessingError(Exception):
    pass


class DocumentProcessor:
    def __init__(
        self,
        session: AsyncSession,
        repository: DocumentRepository,
        storage: FileStorage,
        extraction_service: DocumentExtractionService,
        section_repository: DocumentSectionRepository,
    ) -> None:
        self.session = session
        self.repository = repository
        self.storage = storage
        self.extraction_service = extraction_service
        self.section_repository = section_repository

    async def process(self, document_id: UUID) -> bool:
        document = await self.repository.get_by_id_internal(document_id)

        if document is None:
            return False

        if document.status == DocumentStatus.READY:
            return True

        try:
            await self.repository.mark_processing(document)
            await self.session.commit()

            file_bytes = await asyncio.to_thread(
                self.storage.read,
                document.storage_key,
            )

            parsed_document = await asyncio.to_thread(
                self.extraction_service.extract,
                document.filename,
                file_bytes,
            )

            await self.section_repository.replace_for_document(
                document.id,
                parsed_document.sections,
            )

            await self.repository.mark_ready(
                document,
                parsed_document.page_count,
            )
            await self.session.commit()

            return True

        except Exception as error:
            await self.session.rollback()

            document = await self.repository.get_by_id_internal(document_id)

            if document is not None:
                await self.repository.mark_failed(
                    document,
                    str(error),
                )
                await self.session.commit()

            raise DocumentProcessingError(f"Could not process document: {document_id}") from error
