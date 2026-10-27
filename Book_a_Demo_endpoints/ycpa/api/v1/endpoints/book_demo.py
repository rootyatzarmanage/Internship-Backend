from datetime import date

from fastapi import APIRouter, Query, Request, status

from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.book_demo import BookDemoRequest
from ycpa.schemas.responses.book_demo import BookDemoResponse, CalendarResponse, SlotsResponse
from ycpa.services.book_demo import BookDemoService

router = APIRouter(prefix="/book-a-demo", tags=["Book a Demo"])


@router.get("/calendar", response_model=SuccessResponse[CalendarResponse],
            summary="Month view: Available / Busy / Unavailable for every day")
async def calendar(
    session: DatabaseSession,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    tz: str = Query("UTC", alias="timezone", max_length=64, description="Visitor IANA timezone, e.g. Asia/Kolkata"),
):
    return SuccessResponse(data=await BookDemoService(session).calendar(year, month, tz))


@router.get("/slots", response_model=SuccessResponse[SlotsResponse],
            summary="'Available Timing' list for a date (booked: 0 = free, 1 = booked)")
async def slots(
    session: DatabaseSession,
    slot_date: date = Query(..., alias="date", description="YYYY-MM-DD in the visitor's timezone"),
    tz: str = Query("UTC", alias="timezone", max_length=64, description="Visitor IANA timezone, e.g. Asia/Kolkata"),
):
    return SuccessResponse(data=await BookDemoService(session).slots(slot_date, tz))


@router.post("", response_model=SuccessResponse[BookDemoResponse], status_code=status.HTTP_201_CREATED,
             summary="Submit the Book A Demo form for the selected slot")
async def book_demo(data: BookDemoRequest, request: Request, session: DatabaseSession):
    result = await BookDemoService(session).create(
        data,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SuccessResponse(message="Your demo is booked. A confirmation email is on its way.", data=result)
