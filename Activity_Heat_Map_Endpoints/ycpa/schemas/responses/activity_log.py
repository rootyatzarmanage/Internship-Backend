from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ActivityLogCategory = Literal[
    "projects",
    "meetings",
    "workspaces",
]


class ActivityLogItemResponse(BaseModel):
    id: int

    actor_id: str
    actor_name: str
    actor_initials: str
    action: str
    resource_type: str
    resource_id: str | None = None
    resource_name: str | None = None

    category: ActivityLogCategory

    workspace_id: str | None = None
    workspace_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None

    created_at: datetime

    relative_time: str

    message: str


class ActivityLogResponse(BaseModel):
    filter: Literal[
        "all",
        "projects",
        "meetings",
        "workspaces",
    ]

    activities: list[ActivityLogItemResponse]

    total: int

    limit: int
    offset: int

    has_more: bool