from personal_document_intelligence_api.documents.models import (
    DocumentSection,
    ExtractionMethod,
)
from personal_document_intelligence_api.retrieval.chunking import (
    chunk_document_sections,
)


def test_chunk_sections_with_overlap() -> None:
    section = DocumentSection(
        text="one two three four five six seven",
        page_number=2,
        extraction_method=ExtractionMethod.NATIVE,
    )

    chunks = chunk_document_sections(
        [section],
        max_words=4,
        overlap_words=1,
    )

    assert [chunk.text for chunk in chunks] == [
        "one two three four",
        "four five six seven",
    ]
    assert chunks[0].page_number == 2
    assert chunks[0].section_position == 0


def test_chunking_preserves_section_boundaries() -> None:
    sections = [
        DocumentSection(
            text="first section",
            page_number=1,
            extraction_method=ExtractionMethod.NATIVE,
        ),
        DocumentSection(
            text="second section",
            page_number=2,
            extraction_method=ExtractionMethod.OCR,
        ),
    ]

    chunks = chunk_document_sections(sections)

    assert len(chunks) == 2
    assert chunks[0].section_position == 0
    assert chunks[1].section_position == 1
