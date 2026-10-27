import datetime as dt
from typing import Literal

from pydantic import BaseModel

DayStatus = Literal["available", "busy", "unavailable"]


class DayAvailability(BaseModel):
    date: dt.date
    status: DayStatus
    open_slots: int
    total_slots: int


class CalendarResponse(BaseModel):
    year: int
    month: int
    timezone: str
    days: list[DayAvailability]


class TimeSlotResponse(BaseModel):
    starts_at: dt.datetime        # UTC - send this back unchanged when booking
    time: str                     # label in the visitor's timezone, e.g. "10:00 AM"
    booked: int                   # 0 = free, 1 = booked
    available: bool               # True when booked == 0 (button can be clicked)


class SlotsResponse(BaseModel):
    date: dt.date
    timezone: str
    slots: list[TimeSlotResponse]


class BookDemoResponse(BaseModel):
    book_demo_id: str | None = None
    full_name: str
    email: str
    starts_at: dt.datetime
    scheduled_for: str
    timezone: str
    status: str
    opt: int
    calendar_invite: bool         # True when an .ics invite was attached to the email
