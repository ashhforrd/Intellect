import asyncio
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.api.dependencies.knowledge import (
    get_knowledge_graph_extractor,
)
from personal_document_intelligence_api.api.dependencies.rate_limit import (
    enforce_expensive_rate_limit,
)
from personal_document_intelligence_api.api.schemas.knowledge import (
    ConversationGraphRequest,
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
from personal_document_intelligence_api.database.models.project import ProjectRole
from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.knowledge_graph import (
    KnowledgeGraphRepository,
)
from personal_document_intelligence_api.database.repositories.project import ProjectRepository
from personal_document_intelligence_api.database.session import (
    get_database_session,
)
from personal_document_intelligence_api.knowledge.base import (
    KnowledgeGraphExtractor,
)
from personal_document_intelligence_api.knowledge.extractor import (
    KnowledgeGraphExtractionError,
)
from personal_document_intelligence_api.knowledge.models import (
    KnowledgeGraph,
    KnowledgeSource,
)
from personal_document_intelligence_api.knowledge.service import (
    DocumentHasNoChunksError,
    KnowledgeGraphService,
)
from personal_document_intelligence_api.knowledge.validation import (
    InvalidKnowledgeGraphError,
)

router = APIRouter(prefix="/documents", tags=["knowledge"])
conversation_router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def build_knowledge_graph_response(
    graph: KnowledgeGraph,
) -> KnowledgeGraphResponse:
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


@conversation_router.post(
    "/conversation-graph",
    response_model=KnowledgeGraphResponse,
    dependencies=[Depends(enforce_expensive_rate_limit)],
)
async def generate_conversation_graph(
    request: ConversationGraphRequest,
    extractor: Annotated[
        KnowledgeGraphExtractor,
        Depends(get_knowledge_graph_extractor),
    ],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> KnowledgeGraphResponse:
    membership = await ProjectRepository(session).get_membership(request.project_id, owner_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if membership.role == ProjectRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")
    contexts = [
        KnowledgeSource(
            chunk_id=uuid4(),
            text=f"User question: {turn.question}\nGrounded answer: {turn.answer}",
        )
        for turn in request.turns
    ]

    try:
        graph = await asyncio.to_thread(extractor.extract, contexts)
    except KnowledgeGraphExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation graph generation is unavailable",
        ) from error
    except InvalidKnowledgeGraphError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generated conversation graph is invalid",
        ) from error

    return build_knowledge_graph_response(graph)


@router.get(
    "/{document_id}/knowledge-graph",
    response_model=KnowledgeGraphResponse,
)
async def get_knowledge_graph(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
    project_id: UUID,
) -> KnowledgeGraphResponse:
    document_repository = DocumentRepository(session)
    document = await document_repository.get_by_id(
        document_id=document_id,
        owner_id=owner_id,
        project_id=project_id,
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    graph = await KnowledgeGraphRepository(session).get_for_document(
        document_id=document.id,
        owner_id=owner_id,
        project_id=project_id,
    )
    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge graph has not been generated",
        )

    return build_knowledge_graph_response(graph)


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
    project_id: UUID,
) -> KnowledgeGraphResponse:
    membership = await ProjectRepository(session).get_membership(project_id, owner_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if membership.role == ProjectRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")
    document_repository = DocumentRepository(session)
    document = await document_repository.get_by_id(
        document_id=document_id,
        owner_id=owner_id,
        project_id=project_id,
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
            project_id=project_id,
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

    return build_knowledge_graph_response(graph)
