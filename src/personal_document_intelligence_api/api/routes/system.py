from typing import Annotated

from fastapi import APIRouter, Depends

from personal_document_intelligence_api.api.dependencies.auth import get_current_owner_id

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/")
async def get_app_information() -> dict[str, str]:
    return {
        "name": "Personal Document Intelligence API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


@router.get("/session")
async def get_session_identity(
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> dict[str, str]:
    return {"member_id": owner_id}
