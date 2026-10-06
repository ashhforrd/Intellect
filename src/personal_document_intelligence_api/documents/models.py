from dataclasses import dataclass
from enum import StrEnum


class ExtractionMethod(StrEnum):
    NATIVE = "native"
    OCR = "ocr"


@dataclass(frozen=True, slots=True)
class DocumentSection:
    text: str
    extraction_method: ExtractionMethod
    page_number: int | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    filename: str
    file_type: str
    size_bytes: int
    page_count: int | None
    sections: tuple[DocumentSection, ...]

    @property
    def text(self) -> str:
        return "\n\n".join(section.text for section in self.sections)

    @property
    def character_count(self) -> int:
        return len(self.text)

    @property
    def native_section_count(self) -> int:
        return sum(
            section.extraction_method == ExtractionMethod.NATIVE for section in self.sections
        )

    @property
    def ocr_section_count(self) -> int:
        return sum(section.extraction_method == ExtractionMethod.OCR for section in self.sections)


@dataclass(frozen=True, slots=True)
class ValidatedDocumentUpload:
    filename: str
    file_type: str
    size_bytes: int
