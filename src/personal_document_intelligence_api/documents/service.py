from pathlib import Path

from .models import ParsedDocument, ValidatedDocumentUpload
from .ocr import OcrEngine
from .parser import (
    SUPPORTED_EXTENSIONS,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
    parse_document,
)

DEFAULT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


class DocumentValidationError(Exception):
    """Raised when an uploaded document fails validation."""


class InvalidFilenameError(DocumentValidationError):
    """Raised when the document filename is invalid."""


class DocumentTooLargeError(DocumentValidationError):
    """Raised when the document exceeds the size limit."""


class DocumentExtractionService:
    def __init__(
        self,
        ocr_engine: OcrEngine,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self._ocr_engine = ocr_engine
        self._max_file_size_bytes = max_file_size_bytes

    def extract(
        self,
        filename: str,
        file_bytes: bytes,
    ) -> ParsedDocument:
        upload = self.validate(filename, file_bytes)

        return parse_document(
            filename=upload.filename,
            file_bytes=file_bytes,
            ocr_engine=self._ocr_engine,
        )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        safe_filename = filename.replace("\\", "/").split("/")[-1].strip()

        if not safe_filename or safe_filename in {".", ".."}:
            raise InvalidFilenameError("The document filename is invalid")

        if "\x00" in safe_filename:
            raise InvalidFilenameError("The document filename contains invalid characters")

        return safe_filename

    def validate(
        self,
        filename: str,
        file_bytes: bytes,
    ) -> ValidatedDocumentUpload:
        safe_filename = self._sanitize_filename(filename)

        if len(file_bytes) > self._max_file_size_bytes:
            max_size_mb = self._max_file_size_bytes // (1024 * 1024)
            raise DocumentTooLargeError(f"Document size must not exceed {max_size_mb} MB")

        if not file_bytes:
            raise EmptyDocumentError("The document is empty")

        extension = Path(safe_filename).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type: {extension or 'unknown'}"
            )

        return ValidatedDocumentUpload(
            filename=safe_filename,
            file_type=extension.removeprefix("."),
            size_bytes=len(file_bytes),
        )
