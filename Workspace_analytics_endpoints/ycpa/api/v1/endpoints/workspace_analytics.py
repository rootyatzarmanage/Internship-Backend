import logging

from fastapi import APIRouter, Query
from datetime import datetime

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import (
    BaseResponse,
    SuccessResponse,
)
from ycpa.schemas.responses.workspace_analytics import (
    CountResponse,
    ProjectCountResponse,
    LatestMeetingResponse,
    WorkspaceAnalyticsOverviewResponse,
    RecentPaymentResponse
)
from ycpa.services.workspace_analytics import (
    WorkspaceAnalyticsService,
    PaymentAnalyticsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspace_analytics",
    tags=["Workspace Analytics"],
)

@router.get(
    "/workspaces_count",
    response_model=BaseResponse[CountResponse],
    summary="Get total number of workspaces",
)
async def get_workspace_count(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> BaseResponse[CountResponse]:

    service = WorkspaceAnalyticsService(session)

    count = await service.get_workspace_count(
        user_id=current_user.id,
    )

    return SuccessResponse(
        success=True,
        message="Workspace count fetched successfully",
        data=CountResponse(
            count=count,
        ),
    )


@router.get(
    "/projects_count",
    response_model=BaseResponse[CountResponse],
    summary="Get total number of projects",
)
async def get_project_count(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> BaseResponse[CountResponse]:

    service = WorkspaceAnalyticsService(session)

    count = await service.get_project_count(
        user_id=current_user.id,
    )

    return SuccessResponse(
        success=True,
        message="Project count fetched successfully",
        data=CountResponse(
            count=count,
        ),
    )

@router.get(
        "/pim-projects_count",
        response_model=BaseResponse[ProjectCountResponse],
        summary="Get PIM project counts",
)
async def get_pim_project_count(
    session : DatabaseSession,
    current_user : CurrentUser,
)-> BaseResponse[ProjectCountResponse]:
    service = WorkspaceAnalyticsService(session)
    total_count = await service.get_pim_project_count(
        user_id=current_user.id
    )
    active_count = await service.get_active_pim_project_count(
        user_id=current_user.id
    )
    return SuccessResponse(
        success = True,
        message = "PIM Project count fetched successfully",
        data = ProjectCountResponse(
            total_count= total_count,
            active_count= active_count
        )
    )

@router.get(
    "/aim-projects_count",
    response_model=BaseResponse[ProjectCountResponse],
    summary="Get AIM projects counts",
)
async def get_aim_project_count(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> BaseResponse[ProjectCountResponse]:

    service = WorkspaceAnalyticsService(session)
    total_count = await service.get_aim_project_count(
        user_id=current_user.id,
    )
    active_count = await service.get_active_aim_project_count(
        user_id= current_user.id
    )
    return SuccessResponse(
        success=True,
        message="AIM project count fetched successfully",
        data=ProjectCountResponse(
            total_count = total_count,
            active_count = active_count
        ),
    )


@router.get(
    "/meetings_overview",
    response_model=BaseResponse[list[LatestMeetingResponse]],
    summary="Get latest workspace meetings",
)
async def get_latest_meetings(
    session: DatabaseSession,
    current_user: CurrentUser,
    meeting_search: str | None = Query(
        default=None,
        description="Search meetings by title",
    ),
    meeting_limit: int = Query(
        default=5,
        ge=1,
        le=50,
    ),
) -> BaseResponse[list[LatestMeetingResponse]]:

    service = WorkspaceAnalyticsService(session)

    meetings = await service.get_latest_meetings(
        user_id=current_user.id,
        limit=meeting_limit,
        search=meeting_search,
    )

    return SuccessResponse(
        success=True,
        message="Latest meetings fetched successfully",
        data=meetings,
    )

@router.get(
    "/overview",
    response_model=BaseResponse[WorkspaceAnalyticsOverviewResponse],
    summary="Get workspace analytics overview",
)
async def get_workspace_analytics_overview(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> BaseResponse[WorkspaceAnalyticsOverviewResponse]:

    service = WorkspaceAnalyticsService(session)

    data = await service.get_overview_chart(
        user_id=current_user.id,
    )

    return SuccessResponse(
        success=True,
        message="Workspace analytics overview fetched successfully",
        data=data,
    )

@router.get(
    "/payments",
    response_model=BaseResponse[PaymentAnalyticsResponse],
    summary="Get payment analytics",
)
async def get_payment_analytics(
    session: DatabaseSession,
    current_user: CurrentUser,
    year: int = Query(
        default=datetime.now().year,
        description="Payment analytics year",
    ),
) -> BaseResponse[PaymentAnalyticsResponse]:

    service = WorkspaceAnalyticsService(session)

    data = await service.get_payment_analytics(
        user_id=current_user.id,
        year=year,
    )

    return SuccessResponse(
        success=True,
        message="Payment analytics fetched successfully",
        data=data,
    )

@router.get(
    "/payments/recent",
    response_model=BaseResponse[list[RecentPaymentResponse]],
    summary="Get recent payments",
)
async def get_recent_payments(
    session: DatabaseSession,
    current_user: CurrentUser,
    payment_limit: int = Query(
        default=7,
        ge=1,
        le=50,
    ),
) -> BaseResponse[list[RecentPaymentResponse]]:

    service = WorkspaceAnalyticsService(session)

    data = await service.get_recent_payments(
        user_id=current_user.id,
        limit=payment_limit,
    )

    return SuccessResponse(
        success=True,
        message="Recent payments fetched successfully",
        data=data,
    )