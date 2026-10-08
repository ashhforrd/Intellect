from fastapi.testclient import TestClient

from personal_document_intelligence_api.main import create_app


def test_local_frontend_origin_is_allowed() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:5173")
