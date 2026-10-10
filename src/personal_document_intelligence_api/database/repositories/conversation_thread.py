from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.conversation_thread import (
    ConversationThreadRecord,
)
from personal_document_intelligence_api.database.models.conversation_turn import (
    ConversationTurnRecord,
)


class ConversationThreadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        project_id: UUID,
        thread_id: str,
        created_by: UUID,
        title: str = "New conversation",
    ) -> ConversationThreadRecord:
        thread = ConversationThreadRecord(
            id=thread_id,
            project_id=project_id,
            title=title,
            created_by=created_by,
        )
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def get(self, project_id: UUID, thread_id: str) -> ConversationThreadRecord | None:
        return await self.session.get(ConversationThreadRecord, (thread_id, project_id))

    async def list_for_project(
        self, project_id: UUID, *, limit: int = 100
    ) -> Sequence[ConversationThreadRecord]:
        result = await self.session.execute(
            select(ConversationThreadRecord)
            .where(ConversationThreadRecord.project_id == project_id)
            .order_by(ConversationThreadRecord.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def update(
        self,
        thread: ConversationThreadRecord,
        *,
        title: str | None = None,
        is_archived: bool | None = None,
    ) -> ConversationThreadRecord:
        if title is not None:
            thread.title = title
        if is_archived is not None:
            thread.is_archived = is_archived
        thread.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def touch(self, thread: ConversationThreadRecord) -> None:
        thread.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def delete(self, thread: ConversationThreadRecord) -> None:
        await self.session.execute(
            delete(ConversationTurnRecord).where(
                ConversationTurnRecord.project_id == thread.project_id,
                ConversationTurnRecord.thread_id == thread.id,
            )
        )
        await self.session.delete(thread)
        await self.session.flush()
