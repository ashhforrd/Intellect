import httpx
import pytest

from personal_document_intelligence_api.storage import (
    StoredFileNotFoundError,
    SupabaseFileStorage,
)


def build_storage(handler: httpx.MockTransport) -> SupabaseFileStorage:
    return SupabaseFileStorage(
        project_url="https://project.supabase.co",
        service_role_key="secret-key",
        bucket_name="documents",
        client=httpx.Client(
            base_url="https://project.supabase.co",
            transport=handler,
        ),
    )


def test_save_file_to_private_bucket() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/storage/v1/object/documents/projects/123/file.pdf"
        assert request.headers["content-type"] == "application/pdf"
        assert request.headers["x-upsert"] == "true"
        assert request.content == b"content"
        return httpx.Response(200)

    storage = build_storage(httpx.MockTransport(handle))

    storage.save("projects/123/file.pdf", b"content")


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        (
            "document.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("notes.md", "text/markdown"),
        ("notes.markdown", "text/markdown"),
        ("notes.txt", "text/plain"),
    ],
)
def test_save_uses_allowed_document_content_type(filename: str, content_type: str) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == content_type
        return httpx.Response(200)

    storage = build_storage(httpx.MockTransport(handle))

    storage.save(f"projects/123/{filename}", b"content")


def test_read_file_from_private_bucket() -> None:
    storage = build_storage(
        httpx.MockTransport(lambda request: httpx.Response(200, content=b"content"))
    )

    assert storage.read("projects/123/file.pdf") == b"content"


def test_read_missing_file() -> None:
    storage = build_storage(httpx.MockTransport(lambda request: httpx.Response(404)))

    with pytest.raises(StoredFileNotFoundError):
        storage.read("projects/123/missing.pdf")


def test_delete_missing_file_is_idempotent() -> None:
    storage = build_storage(httpx.MockTransport(lambda request: httpx.Response(404)))

    storage.delete("projects/123/missing.pdf")
