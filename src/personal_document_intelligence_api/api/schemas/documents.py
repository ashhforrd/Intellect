from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from personal_document_intelligence_api.database.models.document import (
    DocumentStatus,
)
from personal_document_intelligence_api.documents.models import ExtractionMethod


class DocumentSectionResponse(BaseModel):
    text: str
    page_number: int | None
    extraction_method: ExtractionMethod
    confidence: float | None = Field(default=None, ge=0, le=1)


class DocumentExtractionResponse(BaseModel):
    filename: str
    file_type: str
    size_bytes: int
    page_count: int | None
    character_count: int
    native_section_count: int
    ocr_section_count: int
    sections: list[DocumentSectionResponse]


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    size_bytes: int
    page_count: int | None
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
