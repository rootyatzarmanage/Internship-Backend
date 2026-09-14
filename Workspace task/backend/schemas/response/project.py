from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    status: int
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @field_validator("name")
    @classmethod
    def name_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")
        return v
    
    @field_validator("status")
    @classmethod
    def status_check(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("Status must be either 0 or 1")
        return v
