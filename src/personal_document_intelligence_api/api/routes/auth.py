from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
    get_session_secret,
    owner_id_to_user_id,
    sign_session_id,
)
from personal_document_intelligence_api.api.schemas.auth import LoginRequest, UserResponse
from personal_document_intelligence_api.core.config import Settings, get_settings
from personal_document_intelligence_api.database.repositories.user import UserRepository
from personal_document_intelligence_api.database.session import get_database_session
from personal_document_intelligence_api.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        member_id=f"user:{user.id}",
    )


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    user = await UserRepository(session).get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect",
        )
    response.set_cookie(
        key=settings.anonymous_session_cookie,
        value=sign_session_id(
            str(user.id), get_session_secret(settings)
        ),
        max_age=settings.anonymous_session_max_age_seconds,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
    )
    return user_response(user)


@router.get("/me", response_model=UserResponse)
async def me(
    owner_id: Annotated[str, Depends(get_current_owner_id)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> UserResponse:
    user = await UserRepository(session).get_by_id(owner_id_to_user_id(owner_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    response.delete_cookie(
        settings.anonymous_session_cookie,
        secure=settings.app_env == "production",
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
