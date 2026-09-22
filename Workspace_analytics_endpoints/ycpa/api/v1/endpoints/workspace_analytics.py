import logging

from fastapi import APIRouter, Query

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import BaseResponse, SuccessResponse
from ycpa.schemas.responses.workspace_analytics import (
    WorkspaceAnalyticsResponse,
)
from ycpa.services.workspace_analytics import (
    WorkspaceAnalyticsService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspace_analytics",
    tags=["Workspace Analytics"],
)


@router.get(
    "",
    response_model=BaseResponse[WorkspaceAnalyticsResponse],
    summary="Get workspace admin analytics dashboard",
)
async def get_workspace_analytics(
    session: DatabaseSession,
    current_user: CurrentUser,
    meeting_search: str | None = Query(
        default=None,
        description="Search latest meeting by title",
    ),
    meeting_limit: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
) -> BaseResponse[WorkspaceAnalyticsResponse]:

    service = WorkspaceAnalyticsService(session)

    data = await service.get_dashboard(
        user_id=current_user.id,
        meeting_limit=meeting_limit,
        meeting_search=meeting_search,
    )

    return SuccessResponse(
        success=True,
        message="Workspace analytics fetched successfully",
        data=data,
    )
