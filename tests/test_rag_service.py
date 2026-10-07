from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from personal_document_intelligence_api.rag.generation.base import (
    AnswerGenerator,
)
from personal_document_intelligence_api.rag.service import RagService
from personal_document_intelligence_api.retrieval.models import (
    SemanticSearchResult,
)
from personal_document_intelligence_api.retrieval.search_service import (
    SemanticSearchService,
)


@pytest.mark.asyncio
async def test_rag_retrieves_sources_and_generates_answer() -> None:
    search_service = AsyncMock(spec=SemanticSearchService)
    answer_generator = Mock(spec=AnswerGenerator)
    source = SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Dynamic programming stores repeated subproblem results.",
        page_number=1,
        score=0.9,
    )

    search_service.search.return_value = [source]
    answer_generator.generate.return_value = (
        "Dynamic programming avoids repeated computation. [Source 1]"
    )

    service = RagService(
        search_service=search_service,
        answer_generator=answer_generator,
    )

    result = await service.ask(
        question="What is dynamic programming?",
        owner_id="user-123",
    )

    assert result.sources == (source,)
    assert "[Source 1]" in result.answer
    answer_generator.generate.assert_called_once_with(
        "What is dynamic programming?",
        [source],
    )


@pytest.mark.asyncio
async def test_rag_skips_generation_when_no_sources_found() -> None:
    search_service = AsyncMock(spec=SemanticSearchService)
    answer_generator = Mock(spec=AnswerGenerator)
    search_service.search.return_value = []

    service = RagService(
        search_service=search_service,
        answer_generator=answer_generator,
    )

    result = await service.ask(
        question="Unknown topic",
        owner_id="user-123",
    )

    assert result.sources == ()
    answer_generator.generate.assert_not_called()
