from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from personal_document_intelligence_api.rag.generation.base import (
    AnswerGenerationError,
    AnswerGenerationIncompleteError,
)
from personal_document_intelligence_api.rag.generation.openai import (
    OpenAIAnswerGenerator,
)
from personal_document_intelligence_api.rag.generation.options import GenerationOptions
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
    assert request["reasoning"] == {"effort": "medium"}


def test_request_selection_does_not_change_shared_generator_defaults() -> None:
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text="An answer", status="completed"
    )
    generator = OpenAIAnswerGenerator(client, "gpt-6-luna", 16000)
    generator.generate("First question", [], options=GenerationOptions("gpt-6-astra", "high"))
    generator.generate("Second question", [])
    first, second = [call.kwargs for call in client.responses.create.call_args_list]
    assert (first["model"], first["reasoning"]) == ("gpt-6-astra", {"effort": "high"})
    assert (second["model"], second["reasoning"]) == ("gpt-6-luna", {"effort": "medium"})
    assert generator.model == "gpt-6-luna"


@pytest.mark.parametrize("output_text", ["", "A truncated answer"])
def test_incomplete_answers_are_rejected(output_text: str) -> None:
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text=output_text, status="incomplete"
    )
    generator = OpenAIAnswerGenerator(client, "gpt-6-luna", 16000)
    with pytest.raises(AnswerGenerationIncompleteError):
        generator.generate("Question", [])


def test_failed_response_is_rejected() -> None:
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text="", status="failed")
    with pytest.raises(AnswerGenerationError):
        OpenAIAnswerGenerator(client, "gpt-6-luna", 16000).generate("Question", [])
