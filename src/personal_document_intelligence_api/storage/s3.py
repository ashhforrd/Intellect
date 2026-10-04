from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .base import FileStorage, StorageError, StoredFileNotFoundError


class S3FileStorage(FileStorage):
    def __init__(
        self,
        bucket_name: str,
        region: str,
        client: Any | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = client or boto3.client(
            "s3",
            region_name=region,
        )

    def save(self, key: str, data: bytes) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=data,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageError(f"Could not save file: {key}") from error

    def read(self, key: str) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=key,
            )
            body = response["Body"]

            try:
                return body.read()
            finally:
                body.close()

        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")

            if error_code in {"NoSuchKey", "404"}:
                raise StoredFileNotFoundError(f"Stored file not found: {key}") from error

            raise StorageError(f"Could not read file: {key}") from error
        except BotoCoreError as error:
            raise StorageError(f"Could not read file: {key}") from error

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(
                Bucket=self._bucket_name,
                Key=key,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageError(f"Could not delete file: {key}") from error
