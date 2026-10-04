from typing import Protocol


class StorageError(Exception):
    """Base error for file storage operations."""


class StoredFileNotFoundError(StorageError):
    """Raised when a stored file does not exist."""


class FileStorage(Protocol):
    def save(self, key: str, data: bytes) -> None:
        """Save file data using a storage key."""

    def read(self, key: str) -> bytes:
        """Read file data using a storage key."""

    def delete(self, key: str) -> None:
        """Delete file data using a storage key."""
