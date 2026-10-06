import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import (
    BaseResponse,
    SuccessResponse,
)
from ycpa.schemas.responses.activity_log import (
    ActivityLogResponse,
)
from ycpa.services.activity_log import (
    ActivityLogService,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/activity_log",
    tags=["Activity_Log"],
)


@router.get(
    "",
    response_model=BaseResponse[
        ActivityLogResponse
    ],
    status_code=status.HTTP_200_OK,
    summary="Get activity log",
)
async def get_activity_log(
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
            "Activity category filter"
        ),
    ),

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> BaseResponse[ActivityLogResponse]:

    try:

        service = ActivityLogService(
            session
        )

        data = await service.get_activity_logs(
            current_user=current_user,
            category=filter,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "Activity log fetched successfully",
            extra={
                "user_id": str(
                    current_user.id
                ),
                "filter": filter,
                "limit": limit,
                "offset": offset,
            },
        )

        return SuccessResponse(
            success=True,
            message=(
                "Activity log fetched successfully"
            ),
            data=data,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch activity log",
            extra={
                "user_id": str(
                    current_user.id
                ),
                "filter": filter,
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Failed to fetch activity log.",
        )