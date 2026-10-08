from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.jobs import get_job_queue
from personal_document_intelligence_api.api.dependencies.storage import (
    get_file_storage,
)
from personal_document_intelligence_api.api.schemas.documents import (
    DocumentExtractionResponse,
    DocumentResponse,
    DocumentSectionResponse,
    StoredDocumentSectionResponse,
)
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_section import (
    DocumentSectionRepository,
)
from personal_document_intelligence_api.database.session import (
    get_database_session,
)
from personal_document_intelligence_api.documents.deletion_service import (
    DocumentDeletionService,
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
from personal_document_intelligence_api.documents.upload_service import (
    DocumentUploadService,
)
from personal_document_intelligence_api.jobs.base import JobQueue, JobQueueError
from personal_document_intelligence_api.storage import FileStorage, StorageError

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


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Document to upload")],
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    storage: Annotated[
        FileStorage,
        Depends(get_file_storage),
    ],
    job_queue: Annotated[
        JobQueue,
        Depends(get_job_queue),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> DocumentResponse:
    try:
        file_bytes = await file.read(DEFAULT_MAX_FILE_SIZE_BYTES + 1)
    finally:
        await file.close()

    try:
        document_upload = await run_in_threadpool(
            extraction_service.validate,
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

    repository = DocumentRepository(session)
    upload_service = DocumentUploadService(
        session=session,
        repository=repository,
        storage=storage,
    )

    try:
        document = await upload_service.upload(
            owner_id=owner_id,
            file_bytes=file_bytes,
            document_upload=document_upload,
        )
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is unavailable",
        ) from error

    try:
        await run_in_threadpool(
            job_queue.publish_document_processing,
            document.id,
        )
    except JobQueueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document was stored, but processing could not be queued",
        ) from error

    return DocumentResponse.model_validate(document)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents(
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    repository = DocumentRepository(session)

    documents = await repository.list_by_owner(
        owner_id=owner_id,
        limit=limit,
        offset=offset,
    )

    return [DocumentResponse.model_validate(document) for document in documents]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> DocumentResponse:
    repository = DocumentRepository(session)

    document = await repository.get_by_id(
        document_id=document_id,
        owner_id=owner_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    storage: Annotated[
        FileStorage,
        Depends(get_file_storage),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> Response:
    repository = DocumentRepository(session)
    deletion_service = DocumentDeletionService(
        session=session,
        repository=repository,
        storage=storage,
    )

    try:
        deleted = await deletion_service.delete(
            document_id=document_id,
            owner_id=owner_id,
        )
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is unavailable",
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[FileStorage, Depends(get_file_storage)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> StreamingResponse:
    repository = DocumentRepository(session)
    document = await repository.get_by_id(document_id=document_id, owner_id=owner_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "md": "text/markdown; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
    }
    try:
        content = await run_in_threadpool(storage.read, document.storage_key)
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is unavailable",
        ) from error

    disposition = "inline" if document.file_type in {"pdf", "md", "txt"} else "attachment"
    return StreamingResponse(
        BytesIO(content),
        media_type=media_types.get(document.file_type, "application/octet-stream"),
        headers={"Content-Disposition": f'{disposition}; filename="{document.filename}"'},
    )


@router.get(
    "/{document_id}/sections",
    response_model=list[StoredDocumentSectionResponse],
)
async def list_document_sections(
    document_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> list[StoredDocumentSectionResponse]:
    document_repository = DocumentRepository(session)

    document = await document_repository.get_by_id(
        document_id=document_id,
        owner_id=owner_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    section_repository = DocumentSectionRepository(session)
    sections = await section_repository.list_for_document(document.id)

    return [StoredDocumentSectionResponse.model_validate(section) for section in sections]
