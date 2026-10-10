from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, delete, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.conversation_thread import (
    ConversationThreadRecord,
)
from personal_document_intelligence_api.database.models.conversation_turn import (
    ConversationTurnRecord,
)
from personal_document_intelligence_api.database.models.user import User


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

    async def participants_for_threads(
        self, project_id: UUID, thread_ids: Sequence[str]
    ) -> dict[str, list[User]]:
        if not thread_ids:
            return {}
        participants = union(
            select(
                ConversationThreadRecord.id.label("thread_id"),
                ConversationThreadRecord.created_by.label("user_id"),
            ).where(
                ConversationThreadRecord.project_id == project_id,
                ConversationThreadRecord.id.in_(thread_ids),
            ),
            select(
                ConversationTurnRecord.thread_id,
                ConversationTurnRecord.author_id,
            ).where(
                ConversationTurnRecord.project_id == project_id,
                ConversationTurnRecord.thread_id.in_(thread_ids),
            ),
        ).subquery()
        result = await self.session.execute(
            select(participants.c.thread_id, User)
            .join(User, User.id == participants.c.user_id)
            .join(
                ConversationThreadRecord,
                (ConversationThreadRecord.id == participants.c.thread_id)
                & (ConversationThreadRecord.project_id == project_id),
            )
            .order_by(
                participants.c.thread_id,
                case((User.id == ConversationThreadRecord.created_by, 0), else_=1),
                User.display_name,
                User.id,
            )
        )
        grouped: dict[str, list[User]] = {}
        for thread_id, user in result.all():
            grouped.setdefault(thread_id, []).append(user)
        return grouped

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
