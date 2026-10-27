import asyncio
import calendar as _calendar
import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.email import build_demo_confirmation_email, build_ics, send_email, send_email_with_ics
from ycpa.core.exceptions import BadRequestException, ConflictException, ValidationException
from ycpa.models.enquiry import BookDemo
from ycpa.repositories.book_demo import BookDemoRepository
from ycpa.schemas.requests.book_demo import BookDemoRequest
from ycpa.schemas.responses.book_demo import (
    BookDemoResponse,
    CalendarResponse,
    DayAvailability,
    SlotsResponse,
    TimeSlotResponse,
)
from ycpa.services.base import BaseService
from ycpa.services.notification import notify

logger = logging.getLogger(__name__)
_tasks: set = set()
SUBJECT = "Your Yatzar Manage demo is booked"


def get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError, OSError):
        raise ValidationException("Invalid timezone", details={"timezone": name})


def _start_of_day_utc(day: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc)


def _time_label(dt_utc: datetime, tz: ZoneInfo) -> str:
    return dt_utc.astimezone(tz).strftime("%I:%M %p").lstrip("0")


def _when_label(dt_utc: datetime, tz: ZoneInfo) -> str:
    local = dt_utc.astimezone(tz)
    return f"{local:%A}, {local.day} {local:%B %Y} at {_time_label(dt_utc, tz)}"


class BookDemoService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = BookDemoRepository(session)
        self.s = s = get_settings()
        self.biz_tz = get_zone(s.BOOKING_TIMEZONE)
        self.slot_times = sorted(time.fromisoformat(t.strip()) for t in s.BOOKING_SLOT_TIMES.split(",") if t.strip())
        self.weekdays = {int(d) for d in s.BOOKING_WORKING_WEEKDAYS.split(",") if d.strip()}
        self.duration = timedelta(minutes=s.BOOKING_DURATION_MINUTES)
        self.min_notice = timedelta(hours=s.BOOKING_MIN_NOTICE_HOURS)
        self.max_advance = timedelta(days=s.BOOKING_MAX_ADVANCE_DAYS)

    def _slot_starts(self, start_utc: datetime, end_utc: datetime) -> list[datetime]:
        """Every demo slot (UTC) with start_utc <= slot < end_utc. Slots are defined in the business timezone."""
        day = start_utc.astimezone(self.biz_tz).date()
        last = (end_utc - timedelta(microseconds=1)).astimezone(self.biz_tz).date()
        out: list[datetime] = []
        while day <= last:
            if day.weekday() in self.weekdays:
                for t in self.slot_times:
                    s = datetime.combine(day, t, tzinfo=self.biz_tz).astimezone(timezone.utc)
                    if start_utc <= s < end_utc:
                        out.append(s)
            day += timedelta(days=1)
        return sorted(out)

    def _window(self) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        return now + self.min_notice, now + self.max_advance

    async def calendar(self, year: int, month: int, tz_name: str) -> CalendarResponse:
        tz = get_zone(tz_name)
        first = date(year, month, 1)
        start = _start_of_day_utc(first, tz)
        end = _start_of_day_utc(date(year + (month == 12), month % 12 + 1, 1), tz)

        booked = await self.repo.count_by_slot(start, end)
        earliest, latest = self._window()

        per_day: dict[date, list[int]] = {}
        for s in self._slot_starts(start, end):
            if not earliest <= s <= latest:
                continue
            d = per_day.setdefault(s.astimezone(tz).date(), [0, 0])
            d[0] += 1
            d[1] += 0 if booked.get(s, 0) > 0 else 1

        days = []
        for n in range(_calendar.monthrange(year, month)[1]):
            day = first + timedelta(days=n)
            total, open_ = per_day.get(day, [0, 0])
            status = "unavailable" if total == 0 else "busy" if open_ == 0 else "available"
            days.append(DayAvailability(date=day, status=status, open_slots=open_, total_slots=total))
        return CalendarResponse(year=year, month=month, timezone=tz_name, days=days)

    async def slots(self, day: date, tz_name: str) -> SlotsResponse:
        tz = get_zone(tz_name)
        start = _start_of_day_utc(day, tz)
        end = _start_of_day_utc(day + timedelta(days=1), tz)

        booked = await self.repo.count_by_slot(start, end)
        earliest, latest = self._window()

        items = []
        for s in self._slot_starts(start, end):
            if not earliest <= s <= latest:
                continue
            is_booked = 1 if booked.get(s, 0) > 0 else 0
            items.append(TimeSlotResponse(starts_at=s, time=_time_label(s, tz), booked=is_booked, available=not is_booked))
        return SlotsResponse(date=day, timezone=tz_name, slots=items)

    async def create(self, data: BookDemoRequest, ip: str | None, user_agent: str | None) -> BookDemoResponse:
        tz = get_zone(data.timezone)
        starts_at = data.starts_at.astimezone(timezone.utc).replace(microsecond=0)

        if not self._slot_starts(starts_at, starts_at + timedelta(seconds=1)):
            raise BadRequestException("Selected time is not a valid demo slot")
        earliest, latest = self._window()
        if not earliest <= starts_at <= latest:
            raise BadRequestException("Selected time is no longer available. Please choose another.")

        # One demo per slot: serialise concurrent requests for the same slot, then re-check.
        await self.repo.lock_slot(starts_at)
        if await self.repo.count_slot(starts_at) >= 1:
            raise ConflictException("This time slot has just been booked. Please choose another.")

        demo = await self.repo.create(BookDemo(
            id=uuid.uuid4(), name=data.full_name, email=str(data.email).lower(),
            phone_code=data.phone_code, phone=data.phone, company=data.company, country=data.country,
            description=data.description, opt=data.opt, preferred_at=starts_at,
            visitor_timezone=data.timezone, status="new",
        ))
        await self.log_audit("book_demo.create", "book_demo", str(demo.id), None,
                             payload={"book_demo_id": demo.book_demo_id}, ip_address=ip, user_agent=user_agent)
        await self.session.commit()

        scheduled_for = _when_label(starts_at, tz)
        await notify(self.session, "book_demo", f"New demo booking {demo.book_demo_id}", {
            "Booking ID": demo.book_demo_id, "Name": demo.name, "Email": demo.email,
            "Phone": f"{demo.phone_code} {demo.phone}", "Company": demo.company, "Country": demo.country,
            "Notes": demo.description or "-", "Calendar invite": "Yes" if demo.opt == 1 else "No",
            "Demo time": f"{_when_label(starts_at, self.biz_tz)} ({self.biz_tz.key})",
            "Visitor time": f"{scheduled_for} ({data.timezone})",
        })
        self._email_visitor(demo, starts_at, scheduled_for, data.timezone)

        return BookDemoResponse(
            book_demo_id=demo.book_demo_id, full_name=demo.name, email=demo.email, starts_at=starts_at,
            scheduled_for=scheduled_for, timezone=data.timezone, status=demo.status,
            opt=demo.opt, calendar_invite=demo.opt == 1,
        )

    def _email_visitor(self, demo: BookDemo, starts_at: datetime, scheduled_for: str, tz_name: str) -> None:
        """Fire-and-forget: a mail problem must not fail a booking that is already saved."""
        html = build_demo_confirmation_email(demo.name, scheduled_for, tz_name, demo.book_demo_id)
        if demo.opt == 1:
            ics = build_ics(
                uid=f"{demo.book_demo_id or demo.id}@yatzarmanage", starts_at=starts_at, ends_at=starts_at + self.duration,
                summary="Yatzar Manage demo",
                description=f"Booking ID: {demo.book_demo_id}\nOur team will walk you through the platform.",
                location=self.s.BOOKING_MEETING_URL, organizer_email=self.s.BOOKING_ORGANIZER_EMAIL or self.s.SMTP_FROM,
                attendee_name=demo.name, attendee_email=demo.email,
            )
            coro = send_email_with_ics(demo.email, SUBJECT, html, ics)
        else:
            coro = send_email(demo.email, SUBJECT, html)
        task = asyncio.create_task(self._safe(coro))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)

    @staticmethod
    async def _safe(coro) -> None:
        try:
            await coro
        except Exception:  # noqa: BLE001
            logger.exception("Demo confirmation email failed")
