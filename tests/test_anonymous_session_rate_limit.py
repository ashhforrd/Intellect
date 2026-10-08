from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.rate_limit import (
    enforce_expensive_rate_limit,
    get_rate_limiter,
)
from personal_document_intelligence_api.core.config import get_settings


def create_test_app() -> FastAPI:
    settings = get_settings().model_copy(
        update={
            "anonymous_session_secret": SecretStr("test-secret"),
            "expensive_rate_limit_requests": 2,
            "expensive_rate_limit_window_seconds": 3600,
        }
    )
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings

    @app.get("/limited")
    def limited_endpoint(
        owner_id: Annotated[str, Depends(get_current_owner_id)],
        rate_limit_guard: Annotated[
            None,
            Depends(enforce_expensive_rate_limit),
        ],
    ) -> dict[str, str]:
        return {"owner_id": owner_id}

    return app


def test_anonymous_session_is_stable_and_rate_limited() -> None:
    get_rate_limiter.cache_clear()
    client = TestClient(create_test_app())

    first = client.get("/limited")
    second = client.get("/limited")
    rejected = client.get("/limited")

    assert first.status_code == 200
    assert "HttpOnly" in first.headers["set-cookie"]
    assert second.json()["owner_id"] == first.json()["owner_id"]
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert rejected.status_code == 429
    assert rejected.headers["Retry-After"]
