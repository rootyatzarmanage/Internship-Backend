import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from ycpa.core.auth.dependencies import get_optional_user
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.repositories.page_visited import PageVisitedRepository
from ycpa.schemas.requests.page_visited import PageVisitedRequest
from ycpa.schemas.responses.page_visited import (
    PageVisitedResponse, 
    PageVisitedFilterOptionsResponse,
    MetricResponse,
    AverageVisitingTimeResponse,
    AcquisitionChannelResponse,
    AcquisitionChannelItem,
    AcquisitionChannelMonthResponse,
    DeviceSessionResponse,
    DeviceSessionItem,
    UniqueVisitorsResponse,
    TotalPageViewsResponse,


)
from ycpa.services.page_visited import PageVisitedService
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.core.schemas.responses import BaseResponse
from ycpa.core.auth.dependencies import SuperAdminUser


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/page_visited",
    tags=["Page_Visited"],
)


@router.post(
    "",
    response_model=BaseResponse[PageVisitedResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record a page visit",
)
async def create_page_visited(
    request: Request,
    payload: PageVisitedRequest,
    session: DatabaseSession,
    current_user=Depends(get_optional_user),
) -> BaseResponse[PageVisitedResponse]:

    try:
        user_id: uuid.UUID | None = None
        if current_user is not None:
            user_id = current_user.id
        repository = PageVisitedRepository(session)
        service = PageVisitedService(repository)
        page_visit = await service.create_page_visit(
            request=request,
            payload=payload,
            user_id=user_id,
        )
        logger.info(
            "Page visit recorded successfully",
            extra={
                "page_visit_id": str(page_visit.id),
                "page_name": payload.page_name,
                "user_id": (
                    str(user_id)
                    if user_id
                    else None
                ),
            },
        )
        page_visit_response = PageVisitedResponse.model_validate(page_visit)
        return SuccessResponse(
            success=True,
            message= "Page visit recorded Successfully",
            data = page_visit_response
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to record page visit",
            extra={
                "page_name": payload.page_name,
                "page_url": payload.page_url,
                "user_id": (
                    str(current_user.id)
                    if current_user is not None
                    else None
                ),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record page visit.",
        )

@router.get(
    "",
    response_model=BaseResponse[
        list[PageVisitedResponse]
    ],
    status_code=status.HTTP_200_OK,
    summary="Get page visits with filters",
)
async def get_page_visits(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    country_name: str | None = Query(
        default=None,
        description="Filter page visits by country",
    ),
    page_name: str | None = Query(
        default=None,
        description="Filter page visits by page",
    ),
) -> BaseResponse[list[PageVisitedResponse]]:

    try:

        repository = PageVisitedRepository(session)

        service = PageVisitedService(repository)
        page_visits = await service.get_page_visits(
            country_name=country_name,
            page_name=page_name,
        )

        logger.info(
            "Page visits fetched successfully",
            extra={
                "country_name": country_name,
                "page_name": page_name,
                "count": len(page_visits),
            },
        )
        data = [
            PageVisitedResponse.model_validate(
                page_visit
            )
            for page_visit in page_visits
        ]

        return SuccessResponse(
            success=True,
            message="Page visits fetched successfully.",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch page visits",
            extra={
                "country_name": country_name,
                "page_name": page_name,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch page visits.",
        )

@router.get(
    "/filters",
    response_model=BaseResponse[PageVisitedFilterOptionsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get page visit filter options",
)
async def get_page_visit_filter_options(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[PageVisitedFilterOptionsResponse]:

    try:

        repository = PageVisitedRepository(session)

        service = PageVisitedService(repository)

        countries = await service.get_countries()

        pages = await service.get_pages()

        data = PageVisitedFilterOptionsResponse(
            countries=countries,
            pages=pages,
        )

        return SuccessResponse(
            success=True,
            message="Page visit filter options fetched successfully.",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to fetch page visit filter options"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch page visit filter options.",
        )

@router.get(
    "/unique_visitors",
    response_model=BaseResponse[UniqueVisitorsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get unique visitors",
)
async def get_unique_visitors(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[UniqueVisitorsResponse]:

    try:
        repository = PageVisitedRepository(session)
        service = PageVisitedService(repository)

        data = await service.get_unique_visitors()

        logger.info(
            "Unique visitors fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Unique visitors fetched successfully",
            data=UniqueVisitorsResponse(**data),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch unique visitors",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch unique visitors.",
        )

@router.get(
    "/total_page_views",
    response_model=BaseResponse[TotalPageViewsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get total page views",
)
async def get_total_page_views(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[TotalPageViewsResponse]:

    try:
        repository = PageVisitedRepository(session)
        service = PageVisitedService(repository)

        data = await service.get_total_page_views()

        logger.info(
            "Total page views fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Total page views fetched successfully",
            data=TotalPageViewsResponse(**data),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch total page views",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch total page views.",
        )

@router.get(
    "/average_visiting_time",
    response_model=BaseResponse[AverageVisitingTimeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get average visiting time",
)
async def get_average_visiting_time(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[AverageVisitingTimeResponse]:

    try:
        repository = PageVisitedRepository(session)
        service = PageVisitedService(repository)

        data = await service.get_average_visiting_time()

        logger.info(
            "Average visiting time fetched successfully",
            extra={
                "value": data,
            },
        )

        return SuccessResponse(
            success=True,
            message="Average visiting time fetched successfully",
            data=AverageVisitingTimeResponse(**data),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch average visiting time",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch average visiting time.",
        )

@router.get(
    "/acquisition_channel",
    response_model=BaseResponse[AcquisitionChannelResponse],
    status_code=status.HTTP_200_OK,
    summary="Get acquisition channel distribution for last six months",
)
async def get_acquisition_channel(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[AcquisitionChannelResponse]:

    try:
        repository = PageVisitedRepository(session)

        service = PageVisitedService(
            repository
        )

        months = await service.get_acquisition_channel()

        logger.info(
            "Acquisition channel fetched successfully",
            extra={
                "months_count": len(months),
            },
        )

        data = AcquisitionChannelResponse(
            months=[
                AcquisitionChannelMonthResponse(
                    month=month_data["month"],
                    channels=[
                        AcquisitionChannelItem(
                            channel=channel_data["channel"],
                            count=channel_data["count"],
                        )
                        for channel_data in month_data["channels"]
                    ],
                )
                for month_data in months
            ]
        )

        return SuccessResponse(
            success=True,
            message="Acquisition channel fetched successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch acquisition channel",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch acquisition channel.",
        )


@router.get(
    "/sessions_by_device",
    response_model=BaseResponse[DeviceSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get total page visit sessions grouped by device type",
)
async def get_sessions_by_device(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> BaseResponse[DeviceSessionResponse]:

    try:
        repository = PageVisitedRepository(session)
        service = PageVisitedService(
            repository
        )
        devices = await service.get_session_by_device()
        logger.info(
            "Sessions by device fetched successfully",
            extra={
                "devices_count": len(devices),
            },
        )
        data = DeviceSessionResponse(
            devices=[
                DeviceSessionItem(
                    device=item["device"],
                    sessions=item["sessions"],
                )
                for item in devices
            ]
        )

        return SuccessResponse(
            success=True,
            message="Sessions by device fetched successfully",
            data=data,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to fetch sessions by device",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sessions by device.",
        )