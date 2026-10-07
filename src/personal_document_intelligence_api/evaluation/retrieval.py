from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


class InvalidEvaluationCaseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    hit: bool
    precision: float
    recall: float


def calculate_retrieval_metrics(
    retrieved_chunk_ids: Sequence[UUID],
    relevant_chunk_ids: set[UUID],
) -> RetrievalMetrics:
    if not relevant_chunk_ids:
        raise InvalidEvaluationCaseError("Evaluation case must contain relevant chunks")

    retrieved_ids = set(retrieved_chunk_ids)
    relevant_retrieved = retrieved_ids & relevant_chunk_ids

    precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0.0
    recall = len(relevant_retrieved) / len(relevant_chunk_ids)

    return RetrievalMetrics(
        hit=bool(relevant_retrieved),
        precision=precision,
        recall=recall,
    )
