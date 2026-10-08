from fastapi import APIRouter

from .routes.documents import router as documents_router
from .routes.knowledge import router as knowledge_router
from .routes.questions import router as questions_router
from .routes.search import router as search_router
from .routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(questions_router)
api_router.include_router(knowledge_router)
