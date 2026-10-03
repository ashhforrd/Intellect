from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from personal_document_intelligence_api.api.schemas.documents import (
    DocumentExtractionResponse,
    DocumentSectionResponse,
)
from personal_document_intelligence_api.documents.ocr import TesseractOcrEngine
from personal_document_intelligence_api.documents.parser import (
    DocumentParsingError,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from personal_document_intelligence_api.documents.service import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DocumentExtractionService,
    DocumentTooLargeError,
    InvalidFilenameError,
)

router = APIRouter(prefix="/documents", tags=["documents"])

extraction_service = DocumentExtractionService(
    ocr_engine=TesseractOcrEngine(),
)


@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
)
async def extract_document(
    file: Annotated[UploadFile, File(description="Document to extract")],
) -> DocumentExtractionResponse:
    try:
        file_bytes = await file.read(DEFAULT_MAX_FILE_SIZE_BYTES + 1)
    finally:
        await file.close()

    try:
        document = await run_in_threadpool(
            extraction_service.extract,
            file.filename or "",
            file_bytes,
        )
    except InvalidFilenameError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except DocumentTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(error),
        ) from error
    except UnsupportedDocumentTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(error),
        ) from error
    except (EmptyDocumentError, DocumentParsingError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return DocumentExtractionResponse(
        filename=document.filename,
        file_type=document.file_type,
        size_bytes=document.size_bytes,
        page_count=document.page_count,
        character_count=document.character_count,
        native_section_count=document.native_section_count,
        ocr_section_count=document.ocr_section_count,
        sections=[
            DocumentSectionResponse(
                text=section.text,
                page_number=section.page_number,
                extraction_method=section.extraction_method,
                confidence=section.confidence,
            )
            for section in document.sections
        ],
    )
