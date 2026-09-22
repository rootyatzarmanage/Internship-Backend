import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.workspace_analytics import (
    WorkspaceAnalyticsRepository,
)
from ycpa.schemas.responses.workspace_analytics import (
    LatestMeetingResponse,
    WorkspaceAnalyticsResponse,
    WorkspaceOverviewResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class WorkspaceAnalyticsService(BaseService):
    """Workspace analytics operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = WorkspaceAnalyticsRepository(session)

    async def get_dashboard(
        self,
        user_id: UUID,
        meeting_limit: int = 5,
        meeting_search: str | None = None,
    ) -> WorkspaceAnalyticsResponse:

        counts = await self.repo.get_workspace_counts(
            user_id=user_id,
        )

        meetings = await self.repo.get_latest_meetings(
            user_id=user_id,
            limit=meeting_limit,
            search=meeting_search,
        )

        latest_meetings = [
            LatestMeetingResponse(
                id=meeting.id,
                meeting_title=meeting.name,
                description=meeting.description,
                date=meeting.date,
                members=(
                    (meeting.member_ids or 0)
                    + (meeting.custom_members or 0)
                ),
                groups=meeting.group_ids or 0,
                status=meeting.status,
            )
            for meeting in meetings
        ]

        return WorkspaceAnalyticsResponse(
            overview=WorkspaceOverviewResponse(
                **counts
            ),
            latest_meetings=latest_meetings,
        )
