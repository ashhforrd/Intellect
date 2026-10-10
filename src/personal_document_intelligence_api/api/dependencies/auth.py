import base64
import hashlib
import hmac
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)

DEVELOPMENT_SESSION_SECRET = "intellect-development-session-secret-change-in-production"


def get_session_secret(settings: Settings) -> str:
    if settings.anonymous_session_secret is not None:
        return settings.anonymous_session_secret.get_secret_value()
    if settings.app_env == "development":
        return DEVELOPMENT_SESSION_SECRET
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Session secret is not configured",
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
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    secret = get_session_secret(settings)
    session_id = verify_session_token(
        request.cookies.get(settings.anonymous_session_cookie),
        secret,
    )
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return f"user:{session_id}"


def owner_id_to_user_id(owner_id: str) -> UUID:
    prefix, separator, raw_user_id = owner_id.partition(":")
    if separator != ":" or prefix != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated identity",
        )
    try:
        return UUID(raw_user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated identity",
        ) from error
