from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextChunk:
    text: str
    section_position: int
    chunk_index: int
    page_number: int | None
