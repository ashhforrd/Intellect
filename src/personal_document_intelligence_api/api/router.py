from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.documents import router as documents_router
from .routes.insights import router as insights_router
from .routes.knowledge import conversation_router
from .routes.knowledge import router as knowledge_router
from .routes.projects import router as projects_router
from .routes.questions import router as questions_router
from .routes.search import router as search_router
from .routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(insights_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(questions_router)
api_router.include_router(knowledge_router)
api_router.include_router(conversation_router)
