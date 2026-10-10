from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
    owner_id_to_user_id,
)
from personal_document_intelligence_api.api.dependencies.embeddings import (
    get_embedding_provider,
)
from personal_document_intelligence_api.api.dependencies.generation import (
    get_answer_generator,
)
from personal_document_intelligence_api.api.dependencies.rate_limit import (
    enforce_expensive_rate_limit,
)
from personal_document_intelligence_api.api.schemas.questions import (
    ConversationTurnResponse,
    PromptAuthorResponse,
    QuestionRequest,
    QuestionResponse,
    QuestionSourceResponse,
)
from personal_document_intelligence_api.core.config import (
    Settings,
    get_settings,
)
from personal_document_intelligence_api.database.repositories.conversation_turn import (
    ConversationTurnRepository,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.project import ProjectRepository
from personal_document_intelligence_api.database.repositories.user import UserRepository
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
    rate_limit_guard: Annotated[
        None,
        Depends(enforce_expensive_rate_limit),
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
            project_id=request.project_id,
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

    user = await UserRepository(session).get_by_id(owner_id_to_user_id(owner_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    await ConversationTurnRepository(session).create(
        project_id=request.project_id,
        thread_id=request.thread_id,
        author_id=user.id,
        question=request.question,
        answer=result.answer,
    )
    await session.commit()

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
        author=PromptAuthorResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
        ),
    )


@router.get(
    "/conversations/{project_id}/{thread_id}",
    response_model=list[ConversationTurnResponse],
)
async def list_conversation_turns(
    project_id: UUID,
    thread_id: str,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> list[ConversationTurnResponse]:
    if await ProjectRepository(session).get_for_member(project_id, owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    turns = await ConversationTurnRepository(session).list_for_thread(project_id, thread_id)
    user_repository = UserRepository(session)
    responses: list[ConversationTurnResponse] = []
    for turn in turns:
        author = await user_repository.get_by_id(turn.author_id)
        if author is None:
            continue
        responses.append(
            ConversationTurnResponse(
                id=turn.id,
                project_id=turn.project_id,
                thread_id=turn.thread_id,
                question=turn.question,
                answer=turn.answer,
                created_at=turn.created_at,
                author=PromptAuthorResponse(
                    id=author.id,
                    email=author.email,
                    display_name=author.display_name,
                ),
            )
        )
    return responses
