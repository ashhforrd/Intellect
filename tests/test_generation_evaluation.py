from personal_document_intelligence_api.evaluation.generation import (
    evaluate_citations,
)


def test_evaluate_valid_citations() -> None:
    evaluation = evaluate_citations(
        answer=("Dynamic programming uses states [Source 1] and transitions [Source 2]."),
        source_count=3,
    )

    assert evaluation.has_citations is True
    assert evaluation.citation_precision == 1.0
    assert evaluation.source_coverage == 2 / 3
    assert evaluation.invalid_sources == ()


def test_detect_invalid_citation() -> None:
    evaluation = evaluate_citations(
        answer="The answer is supported here [Source 4].",
        source_count=2,
    )

    assert evaluation.citation_precision == 0.0
    assert evaluation.invalid_sources == (4,)


def test_detect_missing_citations() -> None:
    evaluation = evaluate_citations(
        answer="An answer without evidence.",
        source_count=2,
    )

    assert evaluation.has_citations is False
    assert evaluation.citation_precision == 0.0
