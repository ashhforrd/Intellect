from pathlib import Path

import pytest

from personal_document_intelligence_api.storage import (
    LocalFileStorage,
    StorageError,
    StoredFileNotFoundError,
)


def test_save_and_read_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    storage.save(
        key="documents/123/document.txt",
        data=b"document content",
    )

    result = storage.read("documents/123/document.txt")

    assert result == b"document content"


def test_delete_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    key = "documents/123/document.txt"

    storage.save(key, b"document content")
    storage.delete(key)

    with pytest.raises(StoredFileNotFoundError):
        storage.read(key)


def test_delete_missing_file_is_idempotent(
    tmp_path: Path,
) -> None:
    storage = LocalFileStorage(tmp_path)

    storage.delete("documents/missing.txt")


def test_reject_path_traversal(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(StorageError):
        storage.save(
            key="../outside.txt",
            data=b"unsafe content",
        )


def test_reject_empty_storage_key(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(StorageError):
        storage.save(key="", data=b"content")
