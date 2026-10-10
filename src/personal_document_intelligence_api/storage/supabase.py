from urllib.parse import quote

import httpx

from .base import FileStorage, StorageError, StoredFileNotFoundError


class SupabaseFileStorage(FileStorage):
    def __init__(
        self,
        project_url: str,
        service_role_key: str,
        bucket_name: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = client or httpx.Client(
            base_url=project_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key,
            },
            timeout=60,
        )

    def save(self, key: str, data: bytes) -> None:
        try:
            response = self._client.post(
                self._object_path(key),
                content=data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "x-upsert": "true",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise StorageError(f"Could not save file: {key}") from error

    def read(self, key: str) -> bytes:
        try:
            response = self._client.get(self._object_path(key))
            if response.status_code == 404:
                raise StoredFileNotFoundError(f"Stored file not found: {key}")
            response.raise_for_status()
            return response.content
        except StoredFileNotFoundError:
            raise
        except httpx.HTTPError as error:
            raise StorageError(f"Could not read file: {key}") from error

    def delete(self, key: str) -> None:
        try:
            response = self._client.delete(self._object_path(key))
            if response.status_code != 404:
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise StorageError(f"Could not delete file: {key}") from error

    def _object_path(self, key: str) -> str:
        normalized_key = key.strip("/")
        if not normalized_key or ".." in normalized_key.split("/"):
            raise StorageError("Invalid storage key")
        bucket = quote(self._bucket_name, safe="")
        object_key = quote(normalized_key, safe="/")
        return f"/storage/v1/object/{bucket}/{object_key}"
