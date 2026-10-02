from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceCreateResponse(BaseModel):
    message: str
    workspace_id: UUID
    name: str


class ProjectCreateResponse(BaseModel):
    message: str
    project_id: UUID
    workspace_id: UUID
    name: str


class ActivityItemResponse(BaseModel):
    id: int
    user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    workspace_id: UUID | None
    project_id: UUID | None
    description: str
    changed_from: dict | None
    changed_to: dict | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogsResponse(BaseModel):
    total: int
    activities: list[ActivityItemResponse]