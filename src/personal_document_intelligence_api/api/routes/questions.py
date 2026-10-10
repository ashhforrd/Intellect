from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
    ConversationParticipantResponse,
    ConversationThreadCreate,
    ConversationThreadResponse,
    ConversationThreadUpdate,
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
from personal_document_intelligence_api.database.models.conversation_thread import (
    ConversationThreadRecord,
)
from personal_document_intelligence_api.database.repositories.conversation_thread import (
    ConversationThreadRepository,
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
    if await ProjectRepository(session).get_for_member(request.project_id, owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    user = await UserRepository(session).get_by_id(owner_id_to_user_id(owner_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

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

    thread_repository = ConversationThreadRepository(session)
    thread = await thread_repository.get(request.project_id, request.thread_id)
    if thread is None:
        thread = await thread_repository.create(
            project_id=request.project_id,
            thread_id=request.thread_id,
            created_by=user.id,
            title=request.question.strip()[:120],
        )
    else:
        await thread_repository.touch(thread)
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


async def require_project_member(
    session: AsyncSession,
    project_id: UUID,
    owner_id: str,
) -> None:
    if await ProjectRepository(session).get_for_member(project_id, owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


async def thread_responses(
    session: AsyncSession, project_id: UUID, threads: Sequence[ConversationThreadRecord]
) -> list[ConversationThreadResponse]:
    participants = await ConversationThreadRepository(session).participants_for_threads(
        project_id, [thread.id for thread in threads]
    )
    return [
        ConversationThreadResponse.model_validate(thread).model_copy(
            update={
                "participants": [
                    ConversationParticipantResponse.model_validate(user)
                    for user in participants.get(thread.id, [])
                ]
            }
        )
        for thread in threads
    ]


@router.get(
    "/conversations/{project_id}",
    response_model=list[ConversationThreadResponse],
)
async def list_conversations(
    project_id: UUID,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> list[ConversationThreadResponse]:
    await require_project_member(session, project_id, owner_id)
    threads = await ConversationThreadRepository(session).list_for_project(project_id)
    return await thread_responses(session, project_id, threads)


@router.post(
    "/conversations/{project_id}",
    response_model=ConversationThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    project_id: UUID,
    request: ConversationThreadCreate,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ConversationThreadResponse:
    await require_project_member(session, project_id, owner_id)
    user = await UserRepository(session).get_by_id(owner_id_to_user_id(owner_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    repository = ConversationThreadRepository(session)
    existing = await repository.get(project_id, request.id)
    if existing is not None:
        return (await thread_responses(session, project_id, [existing]))[0]
    thread = await repository.create(
        project_id=project_id,
        thread_id=request.id,
        created_by=user.id,
        title=request.title,
    )
    await session.commit()
    return (await thread_responses(session, project_id, [thread]))[0]


@router.get(
    "/conversations/{project_id}/{thread_id}/metadata",
    response_model=ConversationThreadResponse,
)
async def get_conversation(
    project_id: UUID,
    thread_id: str,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ConversationThreadResponse:
    await require_project_member(session, project_id, owner_id)
    thread = await ConversationThreadRepository(session).get(project_id, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return (await thread_responses(session, project_id, [thread]))[0]


@router.patch(
    "/conversations/{project_id}/{thread_id}",
    response_model=ConversationThreadResponse,
)
async def update_conversation(
    project_id: UUID,
    thread_id: str,
    request: ConversationThreadUpdate,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ConversationThreadResponse:
    await require_project_member(session, project_id, owner_id)
    repository = ConversationThreadRepository(session)
    thread = await repository.get(project_id, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    thread = await repository.update(
        thread,
        title=request.title.strip() if request.title is not None else None,
        is_archived=request.is_archived,
    )
    await session.commit()
    return (await thread_responses(session, project_id, [thread]))[0]


@router.delete(
    "/conversations/{project_id}/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    project_id: UUID,
    thread_id: str,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> Response:
    await require_project_member(session, project_id, owner_id)
    repository = ConversationThreadRepository(session)
    thread = await repository.get(project_id, thread_id)
    if thread is not None:
        await repository.delete(thread)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
