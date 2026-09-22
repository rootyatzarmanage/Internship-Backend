from uuid import UUID

from pydantic import BaseModel


class WorkspaceOverviewResponse(BaseModel):
    workspace_count: int
    project_count: int
    pim_project_count: int
    pim_active_project_count: int
    aim_project_count: int
    aim_active_project_count: int


class LatestMeetingResponse(BaseModel):
    id: UUID
    meeting_title: str
    description: str | None
    date: str
    members: int
    groups: int
    status: str


class WorkspaceAnalyticsResponse(BaseModel):
    overview: WorkspaceOverviewResponse
    latest_meetings: list[LatestMeetingResponse]