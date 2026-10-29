from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.superadmin_bookademo import (
    BookDemoStatus,
    BookDemoView,
    SortOrder,
    SuperadminBookDemoCalendarQuery,
    SuperadminBookDemoListQuery,
    SuperadminBookDemoOverviewQuery,
    SuperadminBookDemoSlotsQuery,
)
from ycpa.schemas.responses.superadmin_bookademo import (
    SuperadminBookDemoCalendarResponse,
    SuperadminBookDemoDetailResponse,
    SuperadminBookDemoListResponse,
    SuperadminBookDemoOverviewResponse,
    SuperadminBookDemoSlotsResponse,
)
from ycpa.services.superadmin_bookademo import SuperadminBookDemoService

router = APIRouter(prefix="/superadmin/book-a-demo", tags=["Superadmin Book a Demo"])


@router.get(
    "/overview",
    response_model=SuccessResponse[SuperadminBookDemoOverviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Overview page: KPI cards, Calendar Invite Preference and Demo Booking Activity",
)
async def overview(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    start_date: date | None = Query(
        None, description="Activity chart start (YYYY-MM-DD, business timezone). Default: today - 3 days"
    ),
    end_date: date | None = Query(
        None, description="Activity chart end (YYYY-MM-DD, business timezone). Default: today + 3 days"
    ),
) -> SuccessResponse[SuperadminBookDemoOverviewResponse]:
    service = SuperadminBookDemoService(session)
    query = SuperadminBookDemoOverviewQuery(start_date=start_date, end_date=end_date)
    result = await service.overview(query)
    return SuccessResponse(success=True, data=result)


@router.get(
    "/calendar",
    response_model=SuccessResponse[SuperadminBookDemoCalendarResponse],
    status_code=status.HTTP_200_OK,
    summary="Demo Calendar: Available / Busy / Unavailable for every day of a month",
)
async def calendar(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    year: int | None = Query(
        None, ge=2020, le=2100, description="Default: current year (business timezone)"
    ),
    month: int | None = Query(
        None, ge=1, le=12, description="Default: current month (business timezone)"
    ),
) -> SuccessResponse[SuperadminBookDemoCalendarResponse]:
    service = SuperadminBookDemoService(session)
    query = SuperadminBookDemoCalendarQuery(year=year, month=month)
    result = await service.calendar(query)
    return SuccessResponse(success=True, data=result)


@router.get(
    "/slots",
    response_model=SuccessResponse[SuperadminBookDemoSlotsResponse],
    status_code=status.HTTP_200_OK,
    summary="Selected day: every slot as booked / free / closed, with who booked it",
)
async def slots(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    slot_date: date = Query(..., alias="date", description="YYYY-MM-DD in the business timezone"),
) -> SuccessResponse[SuperadminBookDemoSlotsResponse]:
    service = SuperadminBookDemoService(session)
    query = SuperadminBookDemoSlotsQuery(slot_date=slot_date)
    result = await service.slots(query)
    return SuccessResponse(success=True, data=result)


@router.get(
    "/countries",
    response_model=SuccessResponse[list[str]],
    status_code=status.HTTP_200_OK,
    summary="Distinct countries for the Country filter",
)
async def countries(
    session: DatabaseSession,
    current_user: SuperAdminUser,
) -> SuccessResponse[list[str]]:
    service = SuperadminBookDemoService(session)
    result = await service.countries()
    return SuccessResponse(success=True, data=result)


@router.get(
    "/export",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    responses={200: {"content": {"text/csv": {}}}},
    summary="Download the filtered bookings as CSV",
)
async def export_bookings(
    request: Request,
    session: DatabaseSession,
    current_user: SuperAdminUser,
    view: BookDemoView = Query("all", description="all | upcoming | cancelled"),
    search: str | None = Query(
        None, max_length=100, description="booking ID, name, email, company, phone or country"
    ),
    start_date: date | None = Query(None, description="Demo start date (YYYY-MM-DD, business timezone)"),
    end_date: date | None = Query(None, description="Demo end date (YYYY-MM-DD, business timezone)"),
    country: str | None = Query(None, max_length=100),
    status: BookDemoStatus | None = Query(None),
    invite: int | None = Query(None, ge=0, le=1, description="1 = invite requested, 0 = not requested"),
    order: SortOrder = Query("asc", description="Sort by demo date & time"),
    page: int = Query(1, ge=1),
    per_page: int = Query(6, ge=1, le=100),
) -> Response:
    service = SuperadminBookDemoService(session)
    query = SuperadminBookDemoListQuery(
        view=view,
        search=search,
        start_date=start_date,
        end_date=end_date,
        country=country,
        status=status,
        invite=invite,
        order=order,
        page=page,
        per_page=per_page,
    )
    filename, content = await service.export_csv(
        query,
        current_user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "",
    response_model=SuccessResponse[SuperadminBookDemoListResponse | SuperadminBookDemoDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List demo bookings or retrieve booking details using booking_id",
    description="Omit booking_id for the filtered, paginated list. Supply booking_id for booking details.",
)
async def list_bookings(
    session: DatabaseSession,
    current_user: SuperAdminUser,
    booking_id: UUID | None = Query(None, description="Optional booking UUID. Omit for the booking list."),
    view: BookDemoView = Query("all", description="all | upcoming | cancelled"),
    search: str | None = Query(
        None, max_length=100, description="booking ID, name, email, company, phone or country"
    ),
    start_date: date | None = Query(None, description="Demo start date (YYYY-MM-DD, business timezone)"),
    end_date: date | None = Query(None, description="Demo end date (YYYY-MM-DD, business timezone)"),
    country: str | None = Query(None, max_length=100),
    status: BookDemoStatus | None = Query(None),
    invite: int | None = Query(None, ge=0, le=1, description="1 = invite requested, 0 = not requested"),
    order: SortOrder = Query("asc", description="Sort by demo date & time"),
    page: int = Query(1, ge=1),
    per_page: int = Query(6, ge=1, le=100),
) -> SuccessResponse[SuperadminBookDemoListResponse | SuperadminBookDemoDetailResponse]:
    service = SuperadminBookDemoService(session)
    if booking_id is not None:
        result = await service.detail(booking_id)
        return SuccessResponse(success=True, data=result)

    query = SuperadminBookDemoListQuery(
        view=view,
        search=search,
        start_date=start_date,
        end_date=end_date,
        country=country,
        status=status,
        invite=invite,
        order=order,
        page=page,
        per_page=per_page,
    )
    result = await service.list_bookings(query)
    return SuccessResponse(success=True, data=result)
