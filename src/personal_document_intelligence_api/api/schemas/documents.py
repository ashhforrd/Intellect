from pydantic import BaseModel, Field

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
