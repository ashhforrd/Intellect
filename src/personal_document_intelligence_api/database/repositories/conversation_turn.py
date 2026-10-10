from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.conversation_turn import (
    ConversationTurnRecord,
)


class ConversationTurnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        project_id: UUID,
        thread_id: str,
        author_id: UUID,
        question: str,
        answer: str,
    ) -> ConversationTurnRecord:
        turn = ConversationTurnRecord(
            project_id=project_id,
            thread_id=thread_id,
            author_id=author_id,
            question=question,
            answer=answer,
        )
        self.session.add(turn)
        await self.session.flush()
        await self.session.refresh(turn)
        return turn

    async def list_for_thread(
        self, project_id: UUID, thread_id: str
    ) -> Sequence[ConversationTurnRecord]:
        result = await self.session.execute(
            select(ConversationTurnRecord)
            .where(
                ConversationTurnRecord.project_id == project_id,
                ConversationTurnRecord.thread_id == thread_id,
            )
            .order_by(ConversationTurnRecord.created_at, ConversationTurnRecord.id)
        )
        return result.scalars().all()
