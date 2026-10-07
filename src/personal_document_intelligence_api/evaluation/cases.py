from dataclasses import dataclass


class InvalidEvaluationCaseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationCase:
    name: str
    question: str
    expected_terms: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidEvaluationCaseError("Evaluation case name must not be empty")

        if not self.question.strip():
            raise InvalidEvaluationCaseError("Evaluation question must not be empty")

        if not self.expected_terms:
            raise InvalidEvaluationCaseError("Evaluation case must contain expected terms")
