from collections.abc import Sequence

from personal_document_intelligence_api.documents.models import DocumentSection

from .models import TextChunk


class InvalidChunkConfigurationError(ValueError):
    pass


def chunk_document_sections(
    sections: Sequence[DocumentSection],
    *,
    max_words: int = 300,
    overlap_words: int = 50,
) -> tuple[TextChunk, ...]:
    if max_words <= 0:
        raise InvalidChunkConfigurationError("max_words must be greater than zero")

    if overlap_words < 0 or overlap_words >= max_words:
        raise InvalidChunkConfigurationError("overlap_words must be between zero and max_words")

    chunks: list[TextChunk] = []

    for section_position, section in enumerate(sections):
        words = section.text.split()

        if not words:
            continue

        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(start + max_words, len(words))

            chunks.append(
                TextChunk(
                    text=" ".join(words[start:end]),
                    section_position=section_position,
                    chunk_index=chunk_index,
                    page_number=section.page_number,
                )
            )

            if end == len(words):
                break

            start = end - overlap_words
            chunk_index += 1

    return tuple(chunks)
