import re
from dataclasses import dataclass

SOURCE_PATTERN = re.compile(r"\[Source (\d+)\]")


@dataclass(frozen=True, slots=True)
class CitationEvaluation:
    has_citations: bool
    citation_precision: float
    source_coverage: float
    cited_sources: tuple[int, ...]
    invalid_sources: tuple[int, ...]


def evaluate_citations(
    answer: str,
    source_count: int,
) -> CitationEvaluation:
    if source_count < 0:
        raise ValueError("source_count must not be negative")

    cited_sources = tuple(sorted({int(match) for match in SOURCE_PATTERN.findall(answer)}))

    valid_sources = tuple(source for source in cited_sources if 1 <= source <= source_count)
    invalid_sources = tuple(
        source for source in cited_sources if source < 1 or source > source_count
    )

    citation_precision = len(valid_sources) / len(cited_sources) if cited_sources else 0.0
    source_coverage = len(valid_sources) / source_count if source_count else 0.0

    return CitationEvaluation(
        has_citations=bool(cited_sources),
        citation_precision=citation_precision,
        source_coverage=source_coverage,
        cited_sources=cited_sources,
        invalid_sources=invalid_sources,
    )
