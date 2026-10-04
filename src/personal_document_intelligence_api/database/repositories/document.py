from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import (
    Document,
    DocumentStatus,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        owner_id: str,
        filename: str,
        file_type: str,
        storage_key: str,
        size_bytes: int,
        page_count: int | None = None,
    ) -> Document:
        document = Document(
            owner_id=owner_id,
            filename=filename,
            file_type=file_type,
            storage_key=storage_key,
            size_bytes=size_bytes,
            page_count=page_count,
            status=DocumentStatus.UPLOADED,
        )

        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)

        return document

    async def get_by_id(
        self,
        document_id: UUID,
        owner_id: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Document]:
        statement = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(statement)

        return result.scalars().all()

    async def delete(
        self,
        document_id: UUID,
        owner_id: str,
    ) -> bool:
        document = await self.get_by_id(
            document_id=document_id,
            owner_id=owner_id,
        )

        if document is None:
            return False

        await self._session.delete(document)
        await self._session.flush()

        return True
