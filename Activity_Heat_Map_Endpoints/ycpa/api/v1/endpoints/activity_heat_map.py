import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import BaseResponse, SuccessResponse
from ycpa.schemas.responses.activity_heat_map import ActivityHeatMapResponse
from ycpa.services.activity_heatmap import ActivityHeatmapService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/activity_heat_map",
    tags=["Activity_Heat_Map"],
)


@router.get(
    "",
    response_model=BaseResponse[ActivityHeatMapResponse],
    status_code=status.HTTP_200_OK,
    summary="Get activity heat map for the last 6 completed months",
)
async def get_activity_heat_map(
    session: DatabaseSession,
    current_user: CurrentUser,

    filter: Literal[
        "all",
        "projects",
        "meetings",
        "workspaces",
    ] = Query(
        default="all",
        alias="filter",
        description=(
            "Activity category filter: "
            "all, projects, meetings or workspaces"
        ),
    ),
) -> BaseResponse[ActivityHeatMapResponse]:

    try:
        service = ActivityHeatmapService(session)

        data = await service.get_activity_heat_map(
            current_user=current_user,
            category=filter,
        )

        logger.info(
            "Activity heat map fetched successfully",
            extra={
                "filter": filter,
                "user_id": str(current_user.id),
            },
        )

        return SuccessResponse(
            success=True,
            message="Activity heat map fetched successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch activity heat map",
            extra={
                "filter": filter,
                "user_id": str(current_user.id),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity heat map.",
        )