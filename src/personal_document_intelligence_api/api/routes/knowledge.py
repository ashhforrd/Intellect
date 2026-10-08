from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.knowledge import (
    get_knowledge_graph_extractor,
)
from personal_document_intelligence_api.api.schemas.knowledge import (
    KnowledgeConceptResponse,
    KnowledgeGraphResponse,
    KnowledgeRelationResponse,
)
from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)
from personal_document_intelligence_api.database.models.document import (
    DocumentStatus,
)
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.knowledge_graph import (
    KnowledgeGraphRepository,
)
from personal_document_intelligence_api.database.session import (
    get_database_session,
)
from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.extractor import (
    KnowledgeGraphExtractionError,
)
from personal_document_intelligence_api.knowledge.service import (
    DocumentHasNoChunksError,
    KnowledgeGraphService,
)
from personal_document_intelligence_api.knowledge.validation import (
    InvalidKnowledgeGraphError,
)

router = APIRouter(prefix="/documents", tags=["knowledge"])


@router.post(
    "/{document_id}/knowledge-graph",
    response_model=KnowledgeGraphResponse,
)
async def generate_knowledge_graph(
    document_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_database_session),
    ],
    extractor: Annotated[
        KnowledgeGraphExtractor,
        Depends(get_knowledge_graph_extractor),
    ],
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
    owner_id: Annotated[
        str,
        Depends(get_current_owner_id),
    ],
) -> KnowledgeGraphResponse:
    document_repository = DocumentRepository(session)
    document = await document_repository.get_by_id(
        document_id=document_id,
        owner_id=owner_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not ready",
        )

    service = KnowledgeGraphService(
        session=session,
        repository=DocumentChunkRepository(session),
        graph_repository=KnowledgeGraphRepository(session),
        extractor=extractor,
        max_chunks=settings.knowledge_graph_max_chunks,
    )

    try:
        graph = await service.generate(
            document_id=document.id,
            owner_id=owner_id,
        )
    except DocumentHasNoChunksError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except KnowledgeGraphExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge graph generation is unavailable",
        ) from error
    except InvalidKnowledgeGraphError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generated knowledge graph is invalid",
        ) from error

    return KnowledgeGraphResponse(
        concepts=[
            KnowledgeConceptResponse(
                id=concept.id,
                label=concept.label,
                description=concept.description,
                source_chunk_ids=list(concept.source_chunk_ids),
            )
            for concept in graph.concepts
        ],
        relations=[
            KnowledgeRelationResponse(
                source_id=relation.source_id,
                target_id=relation.target_id,
                label=relation.label,
                source_chunk_ids=list(relation.source_chunk_ids),
            )
            for relation in graph.relations
        ],
    )
