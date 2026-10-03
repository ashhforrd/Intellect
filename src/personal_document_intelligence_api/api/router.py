from fastapi import APIRouter

from .routes.documents import router as documents_router
from .routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(documents_router)
