from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import get_current_owner_id
from personal_document_intelligence_api.api.schemas.insights import (
    ConversationInsightRequest,
    ConversationInsightResponse,
)
from personal_document_intelligence_api.database.models.project import ProjectRole
from personal_document_intelligence_api.database.repositories.project import ProjectRepository
from personal_document_intelligence_api.database.repositories.project_insight import (
    ProjectInsightRepository,
)
from personal_document_intelligence_api.database.session import get_database_session
from personal_document_intelligence_api.insights.service import build_conversation_insights

router = APIRouter(prefix="/insights", tags=["insights"])


def insight_response(record) -> ConversationInsightResponse:
    return ConversationInsightResponse(
        id=record.id,
        project_id=record.project_id,
        thread_id=record.thread_id,
        takeaways=record.takeaways,
        actions=record.actions,
        created_at=record.created_at,
    )


@router.post("/conversation", response_model=ConversationInsightResponse)
async def generate_conversation_insights(
    request: ConversationInsightRequest,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ConversationInsightResponse:
    membership = await ProjectRepository(session).get_membership(request.project_id, owner_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if membership.role == ProjectRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")

    insights = build_conversation_insights(
        [(turn.question, turn.answer) for turn in request.turns]
    )
    record = await ProjectInsightRepository(session).create(
        project_id=request.project_id,
        thread_id=request.thread_id,
        insights=insights,
    )
    await session.commit()
    return insight_response(record)


@router.get(
    "/conversation/{project_id}/{thread_id}",
    response_model=ConversationInsightResponse,
)
async def get_conversation_insights(
    project_id: UUID,
    thread_id: str,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ConversationInsightResponse:
    if await ProjectRepository(session).get_for_member(project_id, owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    record = await ProjectInsightRepository(session).get_latest(
        project_id=project_id,
        thread_id=thread_id,
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insights not generated")
    return insight_response(record)
