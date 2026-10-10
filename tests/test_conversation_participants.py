from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from personal_document_intelligence_api.api.routes import questions
from personal_document_intelligence_api.database.base import Base
from personal_document_intelligence_api.database.models.conversation_thread import (
    ConversationThreadRecord,
)
from personal_document_intelligence_api.database.models.conversation_turn import (
    ConversationTurnRecord,
)
from personal_document_intelligence_api.database.models.project import Project
from personal_document_intelligence_api.database.models.user import User
from personal_document_intelligence_api.database.repositories.conversation_thread import (
    ConversationThreadRepository,
)


@pytest.mark.asyncio
async def test_participants_include_creator_deduplicate_authors_and_isolate_projects() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            Project.__table__,
            ConversationThreadRecord.__table__,
            ConversationTurnRecord.__table__,
        ],
    )
    with Session(engine) as database:
        project = Project(id=uuid4(), name="Team project")
        other_project = Project(id=uuid4(), name="Other project")
        creator = User(
            id=uuid4(), email="creator@example.com", display_name="Zoe", password_hash="x"
        )
        author = User(
            id=uuid4(), email="author@example.com", display_name="Alex", password_hash="x"
        )
        outsider = User(
            id=uuid4(), email="outsider@example.com", display_name="Pat", password_hash="x"
        )
        database.add_all([project, other_project, creator, author, outsider])
        thread = ConversationThreadRecord(id="shared", project_id=project.id, created_by=creator.id)
        empty_thread = ConversationThreadRecord(
            id="empty", project_id=project.id, created_by=creator.id
        )
        database.add_all([thread, empty_thread])
        for project_id, user_id in [
            (project.id, author.id),
            (project.id, author.id),
            (project.id, creator.id),
            (other_project.id, outsider.id),
        ]:
            database.add(
                ConversationTurnRecord(
                    project_id=project_id,
                    thread_id="shared",
                    author_id=user_id,
                    question="Question",
                    answer="Answer",
                    created_at=datetime.now(UTC),
                )
            )
        database.commit()
        session = AsyncMock(spec=AsyncSession)
        session.execute.side_effect = database.execute
        repository = ConversationThreadRepository(session)

        result = await repository.participants_for_threads(project.id, ["shared", "empty"])

        assert [user.id for user in result["shared"]] == [creator.id, author.id]
        assert [user.id for user in result["empty"]] == [creator.id]
        session.execute.assert_awaited_once()

        responses = await questions.thread_responses(session, project.id, [thread, empty_thread])
        assert [user.display_name for user in responses[0].participants] == ["Zoe", "Alex"]
        assert set(responses[0].participants[0].model_dump()) == {"id", "display_name"}


@pytest.mark.asyncio
async def test_empty_thread_list_does_not_query_participants() -> None:
    session = AsyncMock(spec=AsyncSession)
    assert await ConversationThreadRepository(session).participants_for_threads(uuid4(), []) == {}
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_unauthorized_project_cannot_read_participants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    monkeypatch.setattr(
        questions,
        "require_project_member",
        AsyncMock(side_effect=HTTPException(status_code=404, detail="Project not found")),
    )
    with pytest.raises(HTTPException) as error:
        await questions.list_conversations(uuid4(), session, "user:outsider")
    assert error.value.status_code == 404
    session.execute.assert_not_awaited()
