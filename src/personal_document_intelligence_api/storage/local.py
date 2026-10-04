from pathlib import Path

from .base import FileStorage, StorageError, StoredFileNotFoundError


class LocalFileStorage(FileStorage):
    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory.resolve()
        self._root_directory.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: bytes) -> None:
        destination = self._resolve_key(key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary_file = destination.with_name(f".{destination.name}.tmp")

        try:
            temporary_file.write_bytes(data)
            temporary_file.replace(destination)
        except OSError as error:
            raise StorageError(f"Could not save file: {key}") from error

    def read(self, key: str) -> bytes:
        source = self._resolve_key(key)

        try:
            return source.read_bytes()
        except FileNotFoundError as error:
            raise StoredFileNotFoundError(f"Stored file not found: {key}") from error
        except OSError as error:
            raise StorageError(f"Could not read file: {key}") from error

    def delete(self, key: str) -> None:
        target = self._resolve_key(key)

        try:
            target.unlink(missing_ok=True)
        except OSError as error:
            raise StorageError(f"Could not delete file: {key}") from error

    def _resolve_key(self, key: str) -> Path:
        path = (self._root_directory / key).resolve()

        if path == self._root_directory:
            raise StorageError("Storage key cannot be empty")

        if not path.is_relative_to(self._root_directory):
            raise StorageError("Storage key escapes the storage directory")

        return path
