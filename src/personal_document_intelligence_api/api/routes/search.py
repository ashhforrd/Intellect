from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.embeddings import (
    get_embedding_provider,
)
from personal_document_intelligence_api.api.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResultResponse,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.session import (
    get_database_session,
)
from personal_document_intelligence_api.retrieval.embeddings.base import (
    EmbeddingProvider,
    EmbeddingProviderError,
)
from personal_document_intelligence_api.retrieval.search_service import (
    EmptySearchQueryError,
    SemanticSearchService,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "",
    response_model=list[SemanticSearchResultResponse],
)
async def semantic_search(
    request: SemanticSearchRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    embedding_provider: Annotated[
        EmbeddingProvider,
        Depends(get_embedding_provider),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> list[SemanticSearchResultResponse]:
    service = SemanticSearchService(
        repository=DocumentChunkRepository(session),
        embedding_provider=embedding_provider,
    )

    try:
        results = await service.search(
            query=request.query,
            owner_id=owner_id,
            project_id=request.project_id,
            limit=request.limit,
            document_id=request.document_id,
        )
    except EmptySearchQueryError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except EmbeddingProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is unavailable",
        ) from error

    return [
        SemanticSearchResultResponse(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            text=result.text,
            page_number=result.page_number,
            score=result.score,
        )
        for result in results
    ]
