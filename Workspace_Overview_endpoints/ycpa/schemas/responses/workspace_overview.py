from datetime import date
from uuid import UUID
from pydantic import BaseModel


class WorkspaceProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    project_type: str
    created_at: date | None


class WorkspaceOverviewItemResponse(BaseModel):
    id: UUID
    name: str
    workspace_type: str
    role: str
    project_count: int
    projects: list[WorkspaceProjectResponse]


class WorkspaceOverviewResponse(BaseModel):
    workspaces: list[WorkspaceOverviewItemResponse]
    total_workspaces: int

