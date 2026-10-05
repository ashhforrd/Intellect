from typing import Annotated

from fastapi import Depends, HTTPException, status

from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)


def get_current_owner_id(
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Production authentication is not configured",
        )

    return "local-development-user"
