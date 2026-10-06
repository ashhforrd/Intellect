from functools import lru_cache
from pathlib import Path
from typing import Literal

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
