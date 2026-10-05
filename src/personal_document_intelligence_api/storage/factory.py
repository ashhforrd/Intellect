from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)

from .base import FileStorage, StorageError
from .local import LocalFileStorage
from .s3 import S3FileStorage


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid."""


def create_file_storage(
    settings: Settings | None = None,
) -> FileStorage:
    settings = settings or get_settings()

    if settings.storage_backend == "local":
        return LocalFileStorage(
            root_directory=settings.local_storage_path,
        )

    if not settings.s3_bucket_name:
        raise StorageConfigurationError("S3_BUCKET_NAME is required when using S3 storage")

    return S3FileStorage(
        bucket_name=settings.s3_bucket_name,
        region=settings.aws_region,
    )
