from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_document_intelligence_api.database.models.document import Document
from personal_document_intelligence_api.database.models.project import (
    Project,
    ProjectMember,
    ProjectRole,
)


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, name: str, owner_id: str) -> Project:
        project = Project(name=name)
        self.session.add(project)
        await self.session.flush()
        self.session.add(
            ProjectMember(
                project_id=project.id,
                member_id=owner_id,
                role=ProjectRole.OWNER,
            )
        )
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def ensure_default(self, owner_id: str) -> Project:
        projects = await self.list_for_member(owner_id, limit=1)
        if projects:
            return projects[0]
        return await self.create(name="Personal project", owner_id=owner_id)

    async def list_for_member(
        self,
        member_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Project]:
        statement = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.member_id == member_id)
            .order_by(Project.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_for_member(self, project_id: UUID, member_id: str) -> Project | None:
        statement = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(Project.id == project_id, ProjectMember.member_id == member_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_membership(
        self,
        project_id: UUID,
        member_id: str,
    ) -> ProjectMember | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.member_id == member_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_members(self, project_id: UUID) -> Sequence[ProjectMember]:
        statement = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.created_at)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add_member(
        self,
        *,
        project_id: UUID,
        member_id: str,
        display_name: str | None,
        role: ProjectRole,
    ) -> ProjectMember:
        existing = await self.get_membership(project_id, member_id)
        if existing is not None:
            existing.display_name = display_name or existing.display_name
            existing.role = role
            await self.session.flush()
            return existing
        member = ProjectMember(
            project_id=project_id,
            member_id=member_id,
            display_name=display_name,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_member(self, project_id: UUID, member_id: str) -> bool:
        result = await self.session.execute(
            delete(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == member_id,
                ProjectMember.role != ProjectRole.OWNER,
            )
        )
        await self.session.flush()
        return bool(result.rowcount)

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()

    async def has_documents(self, project_id: UUID) -> bool:
        result = await self.session.execute(
            select(exists().where(Document.project_id == project_id))
        )
        return bool(result.scalar())
