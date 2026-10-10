from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.api.dependencies.auth import get_current_owner_id
from personal_document_intelligence_api.api.schemas.projects import (
    ProjectCreateRequest,
    ProjectMemberCreateRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from personal_document_intelligence_api.database.models.project import ProjectRole
from personal_document_intelligence_api.database.repositories.project import ProjectRepository
from personal_document_intelligence_api.database.session import get_database_session

router = APIRouter(prefix="/projects", tags=["projects"])


async def require_project(
    repository: ProjectRepository,
    project_id: UUID,
    member_id: str,
):
    project = await repository.get_for_member(project_id, member_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def require_owner(
    repository: ProjectRepository,
    project_id: UUID,
    member_id: str,
) -> None:
    membership = await repository.get_membership(project_id, member_id)
    if membership is None or membership.role != ProjectRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project owner access required",
        )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> list[ProjectResponse]:
    repository = ProjectRepository(session)
    await repository.ensure_default(owner_id)
    await session.commit()
    projects = await repository.list_for_member(owner_id)
    return [ProjectResponse.model_validate(project) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ProjectResponse:
    repository = ProjectRepository(session)
    project = await repository.create(name=" ".join(request.name.split()), owner_id=owner_id)
    await session.commit()
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: ProjectUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ProjectResponse:
    repository = ProjectRepository(session)
    project = await require_project(repository, project_id, owner_id)
    membership = await repository.get_membership(project_id, owner_id)
    if membership is None or membership.role == ProjectRole.VIEWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")
    project.name = " ".join(request.name.split())
    await session.commit()
    await session.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> Response:
    repository = ProjectRepository(session)
    project = await require_project(repository, project_id, owner_id)
    await require_owner(repository, project_id, owner_id)
    if await repository.has_documents(project_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete project documents before deleting the project",
        )
    await repository.delete(project)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> list[ProjectMemberResponse]:
    repository = ProjectRepository(session)
    await require_project(repository, project_id, owner_id)
    members = await repository.list_members(project_id)
    return [ProjectMemberResponse.model_validate(member) for member in members]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    request: ProjectMemberCreateRequest,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> ProjectMemberResponse:
    repository = ProjectRepository(session)
    await require_project(repository, project_id, owner_id)
    await require_owner(repository, project_id, owner_id)
    member = await repository.add_member(
        project_id=project_id,
        member_id=request.member_id,
        display_name=request.display_name,
        role=request.role,
    )
    await session.commit()
    return ProjectMemberResponse.model_validate(member)


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    member_id: str,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    owner_id: Annotated[str, Depends(get_current_owner_id)],
) -> Response:
    repository = ProjectRepository(session)
    await require_project(repository, project_id, owner_id)
    await require_owner(repository, project_id, owner_id)
    removed = await repository.remove_member(project_id, member_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owners cannot be removed; transfer ownership first",
        )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
