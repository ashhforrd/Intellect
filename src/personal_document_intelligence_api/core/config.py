from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    sql_echo: bool = False
    local_storage_path: Path = Path("./data/documents")
    storage_backend: Literal["local", "s3"] = "local"
    aws_region: str = "ap-southeast-2"
    s3_bucket_name: str | None = None
    sqs_queue_url: str | None = None
    openai_api_key: SecretStr | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    generation_model: str = "gpt-6-luna"
    generation_max_output_tokens: int = 800
    rag_minimum_score: float = 0.25
    knowledge_graph_model: str = "gpt-6-luna"
    knowledge_graph_max_concepts: int = 20
    knowledge_graph_max_chunks: int = 30
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
