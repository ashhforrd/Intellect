import asyncio
from uuid import UUID

from personal_document_intelligence_api.rag.generation.base import (
    AnswerGenerator,
)
from personal_document_intelligence_api.rag.models import RagAnswer
from personal_document_intelligence_api.retrieval.search_service import (
    SemanticSearchService,
)


class RagService:
    def __init__(
        self,
        search_service: SemanticSearchService,
        answer_generator: AnswerGenerator,
    ) -> None:
        self.search_service = search_service
        self.answer_generator = answer_generator

    async def ask(
        self,
        *,
        question: str,
        owner_id: str,
        document_id: UUID | None = None,
        retrieval_limit: int = 5,
    ) -> RagAnswer:
        sources = await self.search_service.search(
            query=question,
            owner_id=owner_id,
            limit=retrieval_limit,
            document_id=document_id,
        )

        if not sources:
            return RagAnswer(
                answer="The answer could not be found in the documents.",
                sources=(),
            )

        answer = await asyncio.to_thread(
            self.answer_generator.generate,
            question,
            sources,
        )

        return RagAnswer(
            answer=answer,
            sources=tuple(sources),
        )
