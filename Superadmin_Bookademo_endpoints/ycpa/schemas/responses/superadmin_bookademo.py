import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

DayStatus = Literal["available", "busy", "unavailable"]
SlotState = Literal["booked", "free", "closed"]


# ── Overview ─────────────────────────────────────────────────────────────────
class BookDemoKpiResponse(BaseModel):
    total: int                    # Total Demo Bookings
    new: int                      # New Bookings
    upcoming: int                 # Upcoming Demos (not cancelled, demo time >= now)
    cancelled: int                # Cancelled Demos


class InvitePreferenceResponse(BaseModel):
    requested: int                # opt = 1
    not_requested: int            # opt = 0
    requested_percent: int


class ActivityDayResponse(BaseModel):
    date: dt.date                 # scheduled date in the business timezone
    new: int
    cancelled: int


class SuperadminBookDemoOverviewResponse(BaseModel):
    timezone: str
    as_of: dt.datetime
    kpis: BookDemoKpiResponse
    invite_preference: InvitePreferenceResponse
    activity: list[ActivityDayResponse]


# ── Calendar ─────────────────────────────────────────────────────────────────
class CalendarDayResponse(BaseModel):
    date: dt.date
    status: DayStatus
    booked: int                   # active bookings on that day (all slots)
    open_slots: int               # bookable slots still free (inside the notice/advance window)
    total_slots: int              # bookable slots inside the notice/advance window


class SuperadminBookDemoCalendarResponse(BaseModel):
    year: int
    month: int
    timezone: str
    slots_per_day: int
    min_notice_hours: int
    max_advance_days: int
    as_of: dt.datetime
    days: list[CalendarDayResponse]


# ── Selected-day slots ───────────────────────────────────────────────────────
class SlotBookingResponse(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    company: str | None = None


class SlotItemResponse(BaseModel):
    starts_at: dt.datetime        # UTC
    time: str                     # business-timezone label, e.g. "10:00 AM"
    state: SlotState              # booked | free | closed
    outside_window: bool          # booked slot that is outside the new-booking window
    booking: SlotBookingResponse | None = None


class SuperadminBookDemoSlotsResponse(BaseModel):
    date: dt.date
    timezone: str
    title: str                    # "Thursday, 29 October 2026"
    booked: int
    open: int
    slots: list[SlotItemResponse]


# ── List ─────────────────────────────────────────────────────────────────────
class SuperadminBookDemoListItem(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    email: str
    company: str | None = None
    phone_code: str | None = None
    phone: str | None = None
    country: str | None = None
    preferred_at: dt.datetime | None = None
    demo_date: str | None = None          # "29 Oct 2026" (business timezone)
    demo_time: str | None = None          # "10:00 AM"
    visitor_timezone: str | None = None
    status: str
    opt: int
    invite: str                           # Requested | Not requested
    created_at: dt.datetime
    booked_on: str                        # "28 Oct 2026"


class SuperadminBookDemoListResponse(BaseModel):
    items: list[SuperadminBookDemoListItem]
    total: int
    page: int
    per_page: int
    pages: int
    first_item: int                       # for "1–6 of 12"
    last_item: int


# ── Detail (booking popup) ───────────────────────────────────────────────────
class SuperadminBookDemoDetailResponse(BaseModel):
    id: UUID
    book_demo_id: str | None = None
    name: str
    email: str
    company: str | None = None
    phone_code: str | None = None
    phone: str | None = None
    country: str | None = None
    status: str
    opt: int
    invite: str
    description: str | None = None
    message: str | None = None
    preferred_at: dt.datetime | None = None
    business_timezone: str
    business_date: str | None = None
    business_time: str | None = None
    visitor_timezone: str | None = None
    visitor_local_date: str | None = None
    visitor_local_time: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
