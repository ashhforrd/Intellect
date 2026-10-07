from uuid import uuid4

from personal_document_intelligence_api.evaluation.retrieval import (
    calculate_retrieval_metrics,
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
