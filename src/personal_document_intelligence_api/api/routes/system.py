from fastapi import APIRouter

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
