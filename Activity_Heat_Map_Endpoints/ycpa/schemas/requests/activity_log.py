from typing import Literal

from pydantic import BaseModel, Field


ActivityLogFilter = Literal[
    "all",
    "projects",
    "meetings",
    "workspaces",
]


class ActivityLogRequest(BaseModel):
    filter: ActivityLogFilter = Field(
        default="all",
        description=(
            "Activity filter: all, projects, meetings or workspaces"
        ),
    )

    limit: int = Field(
        default=20  ,
        ge=1,
        le=100,
        description="Maximum number of activity records to return",
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of activity records to skip",
    )