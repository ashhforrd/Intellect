from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.project_insight import ProjectInsightRecord
from personal_document_intelligence_api.insights.models import ConversationInsights


class ProjectInsightRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        project_id: UUID,
        thread_id: str,
        insights: ConversationInsights,
    ) -> ProjectInsightRecord:
        record = ProjectInsightRecord(
            project_id=project_id,
            thread_id=thread_id,
            takeaways=[
                {
                    "title": item.title,
                    "explanation": item.explanation,
                    "source_turn_numbers": list(item.source_turn_numbers),
                }
                for item in insights.takeaways
            ],
            actions=[
                {
                    "rank": item.rank,
                    "title": item.title,
                    "rationale": item.rationale,
                    "priority": item.priority,
                    "kind": item.kind,
                    "source_turn_numbers": list(item.source_turn_numbers),
                }
                for item in insights.actions
            ],
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_latest(
        self,
        *,
        project_id: UUID,
        thread_id: str,
    ) -> ProjectInsightRecord | None:
        result = await self.session.execute(
            select(ProjectInsightRecord)
            .where(
                ProjectInsightRecord.project_id == project_id,
                ProjectInsightRecord.thread_id == thread_id,
            )
            .order_by(ProjectInsightRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
