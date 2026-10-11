from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from personal_document_intelligence_api.rag.generation.options import (
    GENERATION_MODELS,
    ReasoningEffort,
    resolve_generation_options,
)


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    sql_echo: bool = False
    local_storage_path: Path = Path("./data/documents")
    storage_backend: Literal["local", "s3", "supabase"] = "local"
    supabase_url: str | None = None
    supabase_service_role_key: SecretStr | None = None
    supabase_storage_bucket: str | None = None
    aws_region: str = "ap-southeast-2"
    s3_bucket_name: str | None = None
    job_queue_backend: Literal["local", "sqs", "redis"] = "local"
    local_queue_path: Path = Path("./data/jobs")
    sqs_queue_url: str | None = None
    redis_url: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    generation_model: str = "gpt-6-luna"
    generation_allowed_models: list[str] = Field(default_factory=lambda: list(GENERATION_MODELS))
    generation_reasoning_effort: ReasoningEffort = "medium"
    generation_max_output_tokens: int = Field(default=16000, ge=1, le=128000)
    rag_minimum_score: float = 0.25
    knowledge_graph_model: str = "gpt-6-luna"
    knowledge_graph_max_concepts: int = 20
    knowledge_graph_max_chunks: int = 30
    anonymous_session_secret: SecretStr | None = None
    anonymous_session_cookie: str = "intellect_session"
    anonymous_session_max_age_seconds: int = 60 * 60 * 24 * 30
    expensive_rate_limit_requests: int = 20
    expensive_rate_limit_window_seconds: int = 60 * 60
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_generation_settings(self) -> "Settings":
        if any(model not in GENERATION_MODELS for model in self.generation_allowed_models):
            raise ValueError("GENERATION_ALLOWED_MODELS contains an unsupported model")
        resolve_generation_options(
            model=None,
            reasoning_effort=None,
            allowed_models=self.generation_allowed_models,
            default_model=self.generation_model,
            default_effort=self.generation_reasoning_effort,
        )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
