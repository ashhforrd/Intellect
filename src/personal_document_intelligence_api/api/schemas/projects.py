from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from personal_document_intelligence_api.database.models.project import ProjectRole


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ProjectUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberCreateRequest(BaseModel):
    member_id: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)
    role: ProjectRole = ProjectRole.EDITOR


class ProjectMemberResponse(BaseModel):
    id: UUID
    member_id: str
    display_name: str | None
    role: ProjectRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
