from uuid import uuid4

from personal_document_intelligence_api.evaluation.cases import (
    RetrievalEvaluationCase,
)
from personal_document_intelligence_api.evaluation.retrieval import (
    calculate_retrieval_metrics,
    evaluate_retrieval_case,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


def test_calculate_retrieval_metrics() -> None:
    relevant_chunk = uuid4()
    irrelevant_chunk = uuid4()
    missed_relevant_chunk = uuid4()

    metrics = calculate_retrieval_metrics(
        retrieved_chunk_ids=[
            relevant_chunk,
            irrelevant_chunk,
        ],
        relevant_chunk_ids={
            relevant_chunk,
            missed_relevant_chunk,
        },
    )

    assert metrics.hit is True
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5


def test_metrics_when_no_relevant_chunk_is_retrieved() -> None:
    metrics = calculate_retrieval_metrics(
        retrieved_chunk_ids=[uuid4()],
        relevant_chunk_ids={uuid4()},
    )

    assert metrics.hit is False
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0


def test_evaluate_retrieval_case_term_coverage() -> None:
    case = RetrievalEvaluationCase(
        name="dynamic-programming",
        question="How do I recognize dynamic programming?",
        expected_terms=(
            "repeated subproblems",
            "state",
            "transition",
        ),
    )
    result = SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=("Dynamic programming uses a state and transition to solve repeated subproblems."),
        page_number=1,
        score=0.9,
    )

    evaluation = evaluate_retrieval_case(case, [result])

    assert evaluation.hit is True
    assert evaluation.term_coverage == 1.0
