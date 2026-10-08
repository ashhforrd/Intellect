from openai import OpenAI

from personal_document_intelligence_api.core.config import Settings, get_settings
from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.extractor import (
    KnowledgeGraphExtractionError,
    OpenAIKnowledgeGraphExtractor,
)


def create_knowledge_graph_extractor(
    settings: Settings | None = None,
) -> KnowledgeGraphExtractor:
    settings = settings or get_settings()

    if settings.openai_api_key is None:
        raise KnowledgeGraphExtractionError("OPENAI_API_KEY is required")

    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
    )

    return OpenAIKnowledgeGraphExtractor(
        client=client,
        model=settings.knowledge_graph_model,
        max_concepts=settings.knowledge_graph_max_concepts,
    )
