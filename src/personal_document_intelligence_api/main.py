from fastapi import FastAPI

from .api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Intelligence Platform",
        description="Understand and learn from documents using OCR and AI.",
        version="0.1.0",
    )

    app.include_router(api_router)

    return app


app = create_app()
