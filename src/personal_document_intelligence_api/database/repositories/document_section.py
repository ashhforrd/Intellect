from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document_section import (
    DocumentSection as DatabaseDocumentSection,
)
from personal_document_intelligence_api.documents.models import (
    DocumentSection as ParsedDocumentSection,
)


class DocumentSectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_for_document(
        self,
        document_id: UUID,
        sections: tuple[ParsedDocumentSection, ...],
    ) -> None:
        statement = delete(DatabaseDocumentSection).where(
            DatabaseDocumentSection.document_id == document_id
        )
        await self.session.execute(statement)

        database_sections = [
            DatabaseDocumentSection(
                document_id=document_id,
                position=position,
                text=section.text,
                page_number=section.page_number,
                extraction_method=section.extraction_method.value,
                confidence=section.confidence,
            )
            for position, section in enumerate(sections)
        ]

        self.session.add_all(database_sections)
        await self.session.flush()

    async def list_for_document(
        self,
        document_id: UUID,
    ) -> Sequence[DatabaseDocumentSection]:
        statement = (
            select(DatabaseDocumentSection)
            .where(DatabaseDocumentSection.document_id == document_id)
            .order_by(DatabaseDocumentSection.position)
        )

        result = await self.session.execute(statement)

        return result.scalars().all()
