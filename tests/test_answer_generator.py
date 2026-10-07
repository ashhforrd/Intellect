from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from personal_document_intelligence_api.rag.generation.openai import (
    OpenAIAnswerGenerator,
)
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)


def test_generate_grounded_answer() -> None:
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text="Dynamic programming stores repeated results. [Source 1]"
    )
    generator = OpenAIAnswerGenerator(
        client=client,
        model="test-model",
        max_output_tokens=500,
    )
    context = SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Dynamic programming stores repeated subproblem results.",
        page_number=1,
        score=0.9,
    )

    answer = generator.generate(
        question="What is dynamic programming?",
        contexts=[context],
    )

    assert answer == ("Dynamic programming stores repeated results. [Source 1]")

    request = client.responses.create.call_args.kwargs
    assert "Dynamic programming stores repeated subproblem results." in request["input"]
    assert request["store"] is False
