import base64
import hashlib
import hmac
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request, Response, status

from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)


def sign_session_id(session_id: str, secret: str) -> str:
    signature = hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{session_id}.{encoded_signature}"


def verify_session_token(token: str | None, secret: str) -> str | None:
    if not token or "." not in token:
        return None
    session_id, signature = token.rsplit(".", 1)
    try:
        UUID(session_id)
    except ValueError:
        return None
    expected = sign_session_id(session_id, secret).rsplit(".", 1)[1]
    return session_id if hmac.compare_digest(signature, expected) else None


def get_current_owner_id(
    response: Response,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if settings.anonymous_session_secret is None:
        if settings.app_env == "development":
            return "local-development-user"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anonymous session secret is not configured",
        )
    secret = settings.anonymous_session_secret.get_secret_value()
    session_id = verify_session_token(
        request.cookies.get(settings.anonymous_session_cookie),
        secret,
    )
    if session_id is None:
        session_id = str(uuid4())
        response.set_cookie(
            key=settings.anonymous_session_cookie,
            value=sign_session_id(session_id, secret),
            max_age=settings.anonymous_session_max_age_seconds,
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
        )
    return f"anonymous:{session_id}"
