from fastapi import FastAPI

from .api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Personal Document Intelligence API",
        description="Ask grounded questions about personal documents.",
        version="0.1.0",
    )

    app.include_router(api_router)

    return app


app = create_app()
