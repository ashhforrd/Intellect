from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Document Intelligence Platform",
        description="Understand and learn from documents using OCR and AI.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()
