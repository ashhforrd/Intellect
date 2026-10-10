from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)

from .base import FileStorage, StorageError
from .local import LocalFileStorage
from .s3 import S3FileStorage
from .supabase import SupabaseFileStorage


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

    if settings.storage_backend == "supabase":
        if not all(
            (
                settings.supabase_url,
                settings.supabase_service_role_key,
                settings.supabase_storage_bucket,
            )
        ):
            raise StorageConfigurationError(
                "SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and "
                "SUPABASE_STORAGE_BUCKET are required when STORAGE_BACKEND=supabase"
            )
        return SupabaseFileStorage(
            project_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key.get_secret_value(),
            bucket_name=settings.supabase_storage_bucket,
        )

    if not settings.s3_bucket_name:
        raise StorageConfigurationError("S3_BUCKET_NAME is required when using S3 storage")

    return S3FileStorage(
        bucket_name=settings.s3_bucket_name,
        region=settings.aws_region,
    )
