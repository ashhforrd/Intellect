from functools import lru_cache

from personal_document_intelligence_api.rag.generation.base import (
    AnswerGenerator,
)
from personal_document_intelligence_api.rag.generation.factory import (
    create_answer_generator,
)


@lru_cache
def get_answer_generator() -> AnswerGenerator:
    return create_answer_generator()
