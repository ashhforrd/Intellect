from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from personal_document_intelligence_api.api.dependencies.auth import get_current_owner_id
from personal_document_intelligence_api.api.routes import questions
from personal_document_intelligence_api.api.schemas.questions import QuestionRequest
from personal_document_intelligence_api.core.config import Settings, get_settings
from personal_document_intelligence_api.rag.generation.base import AnswerGenerationIncompleteError
from personal_document_intelligence_api.rag.generation.options import (
    GenerationOptions,
    resolve_generation_options,
)
from personal_document_intelligence_api.rag.models import RagAnswer


def make_settings() -> Settings:
    return Settings(_env_file=None, database_url="postgresql+psycopg://localhost/test")


@pytest.mark.parametrize(
    ("model", "effort", "allowed"),
    [
        ("unknown-model", "medium", ["gpt-6-luna"]),
        ("gpt-6-astra", "none", ["gpt-6-luna", "gpt-6-astra"]),
        ("gpt-6-sol", "high", ["gpt-6-luna"]),
    ],
)
def test_invalid_or_disabled_model_choices_are_rejected(model, effort, allowed) -> None:
    with pytest.raises(ValueError):
        resolve_generation_options(
            model=model,
            reasoning_effort=effort,
            allowed_models=allowed,
            default_model="gpt-6-luna",
            default_effort="medium",
        )


def test_omitted_choice_uses_configured_defaults() -> None:
    assert resolve_generation_options(
        model=None,
        reasoning_effort=None,
        allowed_models=["gpt-6-sol"],
        default_model="gpt-6-sol",
        default_effort="low",
    ) == GenerationOptions("gpt-6-sol", "low")


def test_switching_model_without_effort_uses_its_default() -> None:
    assert resolve_generation_options(
        model="gpt-6-astra",
        reasoning_effort=None,
        allowed_models=["gpt-6-luna", "gpt-6-astra"],
        default_model="gpt-6-luna",
        default_effort="none",
    ) == GenerationOptions("gpt-6-astra", "medium")


def test_configuration_rejects_invalid_default_effort() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://localhost/test",
            generation_model="gpt-6-astra",
            generation_reasoning_effort="none",
        )


def test_catalog_requires_authentication_and_obeys_allowlist() -> None:
    app = FastAPI()
    app.include_router(questions.router)
    settings = make_settings().model_copy(update={"generation_allowed_models": ["gpt-6-luna"]})
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)
    assert client.get("/questions/models").status_code == 401
    app.dependency_overrides[get_current_owner_id] = lambda: "user:test"
    response = client.get("/questions/models")
    assert response.status_code == 200
    assert response.json()["default_model"] == "gpt-6-luna"
    assert [model["id"] for model in response.json()["models"]] == ["gpt-6-luna"]
    assert response.json()["models"][0]["reasoning_efforts"] == [
        "none",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["success", "invalid", "incomplete", "unauthorized"])
async def test_question_route_validates_forwards_and_preserves_access(
    monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    session = AsyncMock()
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, email="user@example.com", display_name="User")
    project_repository = Mock()
    project_repository.get_for_member = AsyncMock(
        return_value=None if outcome == "unauthorized" else object()
    )
    monkeypatch.setattr(questions, "ProjectRepository", Mock(return_value=project_repository))
    monkeypatch.setattr(
        questions, "UserRepository", Mock(return_value=Mock(get_by_id=AsyncMock(return_value=user)))
    )
    rag = Mock()
    rag.ask = AsyncMock(return_value=RagAnswer(answer="Grounded answer", sources=()))
    if outcome == "incomplete":
        rag.ask.side_effect = AnswerGenerationIncompleteError("Incomplete")
    monkeypatch.setattr(questions, "RagService", Mock(return_value=rag))
    thread_repository = Mock(get=AsyncMock(return_value=object()), touch=AsyncMock())
    turn_repository = Mock(create=AsyncMock())
    monkeypatch.setattr(
        questions, "ConversationThreadRepository", Mock(return_value=thread_repository)
    )
    monkeypatch.setattr(questions, "ConversationTurnRepository", Mock(return_value=turn_repository))
    request = QuestionRequest(
        project_id=uuid4(),
        thread_id="thread",
        question="Question",
        model="gpt-6-astra",
        reasoning_effort="none" if outcome == "invalid" else "high",
    )
    args = (request, session, Mock(), Mock(), f"user:{user_id}", make_settings(), None)
    if outcome == "success":
        response = await questions.ask_question(*args)
        assert response.answer == "Grounded answer"
        assert rag.ask.call_args.kwargs["generation_options"] == GenerationOptions(
            "gpt-6-astra", "high"
        )
        turn_repository.create.assert_awaited_once()
        session.commit.assert_awaited_once()
    else:
        with pytest.raises(HTTPException) as error:
            await questions.ask_question(*args)
        assert (
            error.value.status_code
            == {"invalid": 422, "incomplete": 503, "unauthorized": 404}[outcome]
        )
        if outcome != "incomplete":
            rag.ask.assert_not_awaited()
        turn_repository.create.assert_not_awaited()
        session.commit.assert_not_awaited()
