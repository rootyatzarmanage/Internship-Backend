from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None


class ProjectCreateRequest(BaseModel):
    workspace_id: UUID
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None
    status: str = "active"


