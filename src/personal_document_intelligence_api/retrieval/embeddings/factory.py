from openai import OpenAI

from personal_document_intelligence_api.core.config import Settings, get_settings

from .base import EmbeddingProvider, EmbeddingProviderError
from .openai import OpenAIEmbeddingProvider


def create_embedding_provider(
    settings: Settings | None = None,
) -> EmbeddingProvider:
    settings = settings or get_settings()

    if settings.openai_api_key is None:
        raise EmbeddingProviderError("OPENAI_API_KEY is required")

    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
    )

    return OpenAIEmbeddingProvider(
        client=client,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
