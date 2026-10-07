from openai import OpenAI

from personal_document_intelligence_api.core.config import Settings, get_settings

from .base import AnswerGenerationError, AnswerGenerator
from .openai import OpenAIAnswerGenerator


def create_answer_generator(
    settings: Settings | None = None,
) -> AnswerGenerator:
    settings = settings or get_settings()

    if settings.openai_api_key is None:
        raise AnswerGenerationError("OPENAI_API_KEY is required")

    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
    )

    return OpenAIAnswerGenerator(
        client=client,
        model=settings.generation_model,
        max_output_tokens=settings.generation_max_output_tokens,
    )
