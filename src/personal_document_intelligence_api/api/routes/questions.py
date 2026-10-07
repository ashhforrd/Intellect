from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.embeddings import (
    get_embedding_provider,
)
from personal_document_intelligence_api.api.dependencies.generation import (
    get_answer_generator,
)
from personal_document_intelligence_api.api.schemas.questions import (
    QuestionRequest,
    QuestionResponse,
    QuestionSourceResponse,
)
from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.session import (
    get_database_session,
)
from personal_document_intelligence_api.rag.generation.base import (
    AnswerGenerationError,
    AnswerGenerator,
)
from personal_document_intelligence_api.rag.service import RagService
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
    EmbeddingProviderError,
)
from personal_document_intelligence_api.retrieval.search_service import (
    EmptySearchQueryError,
    SemanticSearchService,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post(
    "",
    response_model=QuestionResponse,
)
async def ask_question(
    request: QuestionRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    embedding_provider: Annotated[
        EmbeddingProvider,
        Depends(get_embedding_provider),
    ],
    answer_generator: Annotated[
        AnswerGenerator,
        Depends(get_answer_generator),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> QuestionResponse:
    search_service = SemanticSearchService(
        repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )
    rag_service = RagService(
        search_service=search_service,
        answer_generator=answer_generator,
        minimum_score=settings.rag_minimum_score,
    )

    try:
        result = await rag_service.ask(
            question=request.question,
            owner_id=owner_id,
            document_id=request.document_id,
            retrieval_limit=request.retrieval_limit,
        )
    except EmptySearchQueryError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except (EmbeddingProviderError, AnswerGenerationError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is unavailable",
        ) from error

    return QuestionResponse(
        answer=result.answer,
        sources=[
            QuestionSourceResponse(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                text=source.text,
                page_number=source.page_number,
                score=source.score,
            )
            for source in result.sources
        ],
    )
