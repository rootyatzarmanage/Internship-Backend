import logging
from enum import Enum
from datetime import date

from fastapi import APIRouter,HTTPException,Query,status
from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.repositories.admin_user import AdminUserRepository
from ycpa.services.admin_user import AdminUserService
from ycpa.schemas.requests.admin_user import UserStatus
from ycpa.schemas.responses.admin_user import (
    UserMetricResponse,
    AdminUserItem,
    AdminUserListResponse,
    VerifiedStatusItem,
    VerifiedStatusResponse,
    UserStatusItem,
    UserStatusResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/admin_user",
    tags=["Admin User"],
)
@router.get(
    "/total_users",
    response_model=SuccessResponse[UserMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get total users",
)
async def get_total_users(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[UserMetricResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = await service.get_total_users()
        return SuccessResponse(
            success=True,
            message=(
                "Total users fetched successfully"
            ),
            data=UserMetricResponse(
                **data
            ),
        )
    except HTTPException:
        raise
    except Exception:

        logger.exception(
            "Failed to fetch total users"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch total users."
            ),
        )

@router.get(
    "/active_users",
    response_model=SuccessResponse[UserMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active users",
)
async def get_active_users(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[UserMetricResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = await service.get_active_users()
        return SuccessResponse(
            success=True,
            message=(
                "Active users fetched successfully"
            ),
            data=UserMetricResponse(
                **data
            ),
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to fetch active users"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch active users."
            ),
        )
    
@router.get(
    "/verified_users",
    response_model=SuccessResponse[UserMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get verified users",
)
async def get_verified_users(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[UserMetricResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = await service.get_verified_users()

        return SuccessResponse(
            success=True,
            message=(
                "Verified users fetched successfully"
            ),
            data=UserMetricResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch verified users"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch verified users."
            ),
        )

@router.get(
    "/new_signups",
    response_model=SuccessResponse[
        UserMetricResponse
    ],
    status_code=status.HTTP_200_OK,
    summary="Get new signups",
)
async def get_new_signups(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[UserMetricResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = await service.get_new_signups()
        return SuccessResponse(
            success=True,
            message=(
                "New signups fetched successfully"
            ),
            data=UserMetricResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch new signups"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch new signups."
            ),
        )

@router.get(
    "/users_list",
    response_model=SuccessResponse[AdminUserListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get admin user list",
)
async def get_admin_users(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    search: str | None = Query(
        None,
        description="Search by User ID, name, or email",
    ),
    name: str | None = Query(
        None,
        description="Filter by user name",
    ),
    email: str | None = Query(
        None,
        description="Filter by email",
    ),
    verified: bool | None = Query(
        None,
        description="Filter by verified status",
    ),
    user_status: UserStatus | None = Query(
        None,
        alias="status",
        description="Filter by user status",
    ),
    start_date: date | None = Query(
        None,
        description="Filter users registered from this date",
    ),
    end_date: date | None = Query(
        None,
        description="Filter users registered up to this date",
    ),
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        6,
        ge=1,
        le=100,
    ),
) -> SuccessResponse[AdminUserListResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = await service.get_users(
            search=search,
            name=name,
            email=email,
            verified=verified,
            status=(
                user_status.value
                if user_status
                else None
            ),
            start_date = start_date,
            end_date = end_date,
            page=page,
            limit=limit,
        )

        logger.info(
            "User list fetched successfully",
            extra={
                "search": search,
                "name": name,
                "email": email,
                "verified": verified,
                "status": (
                    user_status.value
                    if user_status
                    else None
                ),
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
                "page": page,
                "limit": limit,
                "total": data["total"],
            },
        )

        return SuccessResponse(
            success=True,
            message="User list fetched successfully",
            data=AdminUserListResponse(
                **data
            ),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch admin user list",
            extra={
                "search": search,
                "name": name,
                "email": email,
                "verified": verified,
                "status": (
                    user_status.value
                    if user_status
                    else None
                ),
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
                "page": page,
                "limit": limit,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user list.",
        )

@router.get(
    "/verified_status",
    response_model=SuccessResponse[
        VerifiedStatusResponse
    ],
    status_code=status.HTTP_200_OK,
    summary="Get verified status by year",
)
async def get_verified_status(
    session: DatabaseSession,
    current_user: SuperAdminUser,

    year: int = Query(
        ...,
        description="Year",
    ),

) -> SuccessResponse[VerifiedStatusResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        data = (
            await service.get_verified_status(
                year
            )
        )

        response = VerifiedStatusResponse(
            year=data["year"],

            items=[
                VerifiedStatusItem(
                    **item
                )
                for item in data["items"]
            ],
        )

        return SuccessResponse(
            success=True,
            message=(
                "Verified status fetched successfully"
            ),
            data=response,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch verified status",
            extra={
                "year": year,
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch verified status."
            ),
        )

@router.get(
    "/sessions_by_status",
    response_model=SuccessResponse[
        UserStatusResponse
    ],
    status_code=status.HTTP_200_OK,
    summary="Get sessions by status",
)
async def get_sessions_by_status(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[UserStatusResponse]:

    try:
        repository = AdminUserRepository(session)
        service = AdminUserService(repository)
        statuses = await service.get_users_by_status()
        response = UserStatusResponse(
            statuses=[
                UserStatusItem(
                    **item
                )
                for item in statuses
            ]
        )

        return SuccessResponse(
            success=True,
            message=(
                "Sessions by status fetched successfully"
            ),
            data=response,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch sessions by status"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch sessions by status."
            ),
        )