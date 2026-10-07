from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from personal_document_intelligence_api.evaluation.cases import (
    RetrievalEvaluationCase,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


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


@dataclass(frozen=True, slots=True)
class RetrievalCaseResult:
    name: str
    hit: bool
    term_coverage: float
    matched_terms: tuple[str, ...]


def evaluate_retrieval_case(
    case: RetrievalEvaluationCase,
    results: Sequence[SemanticSearchResult],
) -> RetrievalCaseResult:
    retrieved_text = " ".join(result.text.lower() for result in results)

    matched_terms = tuple(term for term in case.expected_terms if term.lower() in retrieved_text)

    return RetrievalCaseResult(
        name=case.name,
        hit=bool(matched_terms),
        term_coverage=len(matched_terms) / len(case.expected_terms),
        matched_terms=matched_terms,
    )
