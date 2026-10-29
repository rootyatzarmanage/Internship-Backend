import calendar as _calendar
import csv
import io
import logging
import math
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.exceptions import NotFoundException, ValidationException
from ycpa.models.enquiry import BookDemo
from ycpa.models.user import User
from ycpa.repositories.superadmin_bookademo import BookDemoFilters, SuperadminBookDemoRepository
from ycpa.schemas.requests.superadmin_bookademo import (
    SuperadminBookDemoCalendarQuery,
    SuperadminBookDemoListQuery,
    SuperadminBookDemoOverviewQuery,
    SuperadminBookDemoSlotsQuery,
)
from ycpa.schemas.responses.superadmin_bookademo import (
    ActivityDayResponse,
    BookDemoKpiResponse,
    CalendarDayResponse,
    InvitePreferenceResponse,
    SlotBookingResponse,
    SlotItemResponse,
    SuperadminBookDemoCalendarResponse,
    SuperadminBookDemoDetailResponse,
    SuperadminBookDemoListItem,
    SuperadminBookDemoListResponse,
    SuperadminBookDemoOverviewResponse,
    SuperadminBookDemoSlotsResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)

EXPORT_LIMIT = 10_000
EXPORT_FIELDS = ["book_demo_id", "name", "email", "phone_code", "phone", "company", "country", "preferred_at",
                 "visitor_timezone", "description", "opt", "status", "created_at", "updated_at", "deleted_at",
                 "message", "id"]


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError, OSError):
        raise ValidationException("Invalid timezone", details={"timezone": name})


def _invite_label(opt: int) -> str:
    return "Requested" if opt == 1 else "Not requested"


def _csv_safe(value) -> str:
    """Stop spreadsheet formula injection from visitor-typed text."""
    text = "" if value is None else value.isoformat() if isinstance(value, datetime) else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


class SuperadminBookDemoService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SuperadminBookDemoRepository(session)
        self.s = s = get_settings()
        self.tz_name = s.BOOKING_TIMEZONE
        self.biz_tz = _zone(self.tz_name)
        self.slot_times = sorted(time.fromisoformat(t.strip()) for t in s.BOOKING_SLOT_TIMES.split(",") if t.strip())
        self.weekdays = {int(d) for d in s.BOOKING_WORKING_WEEKDAYS.split(",") if d.strip()}
        self.min_notice = timedelta(hours=s.BOOKING_MIN_NOTICE_HOURS)
        self.max_advance = timedelta(days=s.BOOKING_MAX_ADVANCE_DAYS)

    # ── time helpers (everything the admin sees is in the business timezone) ──
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _today(self, now: datetime) -> date:
        return now.astimezone(self.biz_tz).date()

    def _day_start_utc(self, day: date) -> datetime:
        return datetime.combine(day, time.min, tzinfo=self.biz_tz).astimezone(timezone.utc)

    def _slot_starts(self, day: date) -> list[datetime]:
        """Every demo slot (UTC) of a business day; slots are defined in the business timezone."""
        if day.weekday() not in self.weekdays:
            return []
        return sorted(datetime.combine(day, t, tzinfo=self.biz_tz).astimezone(timezone.utc) for t in self.slot_times)

    def _window(self, now: datetime) -> tuple[datetime, datetime]:
        return now + self.min_notice, now + self.max_advance

    def _time_label(self, dt_utc: datetime) -> str:
        return dt_utc.astimezone(self.biz_tz).strftime("%I:%M %p").lstrip("0")

    @staticmethod
    def _date_label(dt_utc: datetime, tz: ZoneInfo) -> str:
        return dt_utc.astimezone(tz).strftime("%d %b %Y")

    def _filters(self, q: SuperadminBookDemoListQuery, now: datetime) -> BookDemoFilters:
        return BookDemoFilters(
            now=now, view=q.view, search=q.search,
            start_utc=self._day_start_utc(q.start_date) if q.start_date else None,
            end_utc=self._day_start_utc(q.end_date + timedelta(days=1)) if q.end_date else None,
            country=q.country, status=q.status, invite=q.invite,
        )

    # ── 1. Overview: KPI cards, Calendar Invite Preference, Demo Booking Activity ──
    async def overview(self, q: SuperadminBookDemoOverviewQuery) -> SuperadminBookDemoOverviewResponse:
        now = self._now()
        today = self._today(now)
        start = q.start_date or (q.end_date - timedelta(days=6) if q.end_date else today - timedelta(days=3))
        end = q.end_date or (q.start_date + timedelta(days=6) if q.start_date else today + timedelta(days=3))

        sm = await self.repo.summary(now)
        rows = await self.repo.status_by_start(self._day_start_utc(start), self._day_start_utc(end + timedelta(days=1)))

        per_day: dict[date, list[int]] = {}
        for starts_at, status in rows:
            d = per_day.setdefault(starts_at.astimezone(self.biz_tz).date(), [0, 0])
            if status == "new":
                d[0] += 1
            elif status == "cancelled":
                d[1] += 1
        activity = [ActivityDayResponse(date=start + timedelta(days=n), new=per_day.get(start + timedelta(days=n), [0, 0])[0],
                                        cancelled=per_day.get(start + timedelta(days=n), [0, 0])[1])
                    for n in range((end - start).days + 1)]

        invites = sm["requested"] + sm["not_requested"]
        return SuperadminBookDemoOverviewResponse(
            timezone=self.tz_name, as_of=now,
            kpis=BookDemoKpiResponse(total=sm["total"], new=sm["new"], upcoming=sm["upcoming"], cancelled=sm["cancelled"]),
            invite_preference=InvitePreferenceResponse(
                requested=sm["requested"], not_requested=sm["not_requested"],
                requested_percent=round(sm["requested"] * 100 / invites) if invites else 0),
            activity=activity,
        )

    # ── 2. Demo Calendar (month): available / busy / unavailable ─────────────
    async def calendar(self, q: SuperadminBookDemoCalendarQuery) -> SuperadminBookDemoCalendarResponse:
        now = self._now()
        today = self._today(now)
        year, month = q.year or today.year, q.month or today.month
        first = date(year, month, 1)
        days_in_month = _calendar.monthrange(year, month)[1]
        start = self._day_start_utc(first)
        end = self._day_start_utc(first + timedelta(days=days_in_month))

        booked = await self.repo.active_by_start(start, end)
        earliest, latest = self._window(now)

        days = []
        for n in range(days_in_month):
            day = first + timedelta(days=n)
            slots = self._slot_starts(day)
            eligible = [s for s in slots if earliest <= s <= latest]
            open_ = [s for s in eligible if s not in booked]
            status = "unavailable" if not eligible else "busy" if not open_ else "available"
            days.append(CalendarDayResponse(date=day, status=status, booked=sum(1 for s in slots if s in booked),
                                            open_slots=len(open_), total_slots=len(eligible)))
        return SuperadminBookDemoCalendarResponse(
            year=year, month=month, timezone=self.tz_name, slots_per_day=len(self.slot_times),
            min_notice_hours=int(self.min_notice.total_seconds() // 3600), max_advance_days=self.max_advance.days,
            as_of=now, days=days)

    # ── 3. Selected-day slots ("3 booked · 4 open") ──────────────────────────
    async def slots(self, q: SuperadminBookDemoSlotsQuery) -> SuperadminBookDemoSlotsResponse:
        now = self._now()
        day = q.slot_date
        booked = await self.repo.active_by_start(self._day_start_utc(day), self._day_start_utc(day + timedelta(days=1)))
        earliest, latest = self._window(now)

        items, n_booked, n_open = [], 0, 0
        for s in self._slot_starts(day):
            in_window = earliest <= s <= latest
            b = booked.get(s)
            if b:
                n_booked += 1
                state = "booked"
            elif in_window:
                n_open += 1
                state = "free"
            else:
                state = "closed"
            items.append(SlotItemResponse(
                starts_at=s, time=self._time_label(s), state=state,
                outside_window=bool(b) and not in_window,
                booking=SlotBookingResponse(id=b.id, book_demo_id=b.book_demo_id, name=b.name, company=b.company) if b else None,
            ))
        return SuperadminBookDemoSlotsResponse(
            date=day, timezone=self.tz_name, title=f"{day:%A}, {day.day} {day:%B %Y}",
            booked=n_booked, open=n_open, slots=items)

    # ── 4. Demo Bookings table ───────────────────────────────────────────────
    def _list_item(self, r: BookDemo) -> SuperadminBookDemoListItem:
        return SuperadminBookDemoListItem(
            id=r.id, book_demo_id=r.book_demo_id, name=r.name, email=r.email, company=r.company,
            phone_code=r.phone_code, phone=r.phone, country=r.country, preferred_at=r.preferred_at,
            demo_date=self._date_label(r.preferred_at, self.biz_tz) if r.preferred_at else None,
            demo_time=self._time_label(r.preferred_at) if r.preferred_at else None,
            visitor_timezone=r.visitor_timezone, status=r.status, opt=r.opt, invite=_invite_label(r.opt),
            created_at=r.created_at, booked_on=self._date_label(r.created_at, self.biz_tz),
        )

    async def list_bookings(self, q: SuperadminBookDemoListQuery) -> SuperadminBookDemoListResponse:
        rows, total = await self.repo.paginate(self._filters(q, self._now()), q.order, q.page, q.per_page)
        first = (q.page - 1) * q.per_page + 1 if rows else 0
        return SuperadminBookDemoListResponse(
            items=[self._list_item(r) for r in rows], total=total, page=q.page, per_page=q.per_page,
            pages=max(1, math.ceil(total / q.per_page)), first_item=first, last_item=first + len(rows) - 1 if rows else 0)

    async def countries(self) -> list[str]:
        return await self.repo.countries()

    # ── 5. Booking popup ─────────────────────────────────────────────────────
    async def detail(self, booking_id: UUID) -> SuperadminBookDemoDetailResponse:
        r = await self.repo.get_by_id(booking_id)
        if not r:
            raise NotFoundException("Booking not found", resource="book_demo")
        v_tz = None
        if r.visitor_timezone:
            try:
                v_tz = ZoneInfo(r.visitor_timezone)
            except (ZoneInfoNotFoundError, ValueError, KeyError, OSError):
                v_tz = None   # keep the stored value visible even if the zone name is no longer valid
        at = r.preferred_at
        return SuperadminBookDemoDetailResponse(
            id=r.id, book_demo_id=r.book_demo_id, name=r.name, email=r.email, company=r.company,
            phone_code=r.phone_code, phone=r.phone, country=r.country, status=r.status, opt=r.opt,
            invite=_invite_label(r.opt), description=r.description, message=r.message, preferred_at=at,
            business_timezone=self.tz_name,
            business_date=self._date_label(at, self.biz_tz) if at else None,
            business_time=self._time_label(at) if at else None,
            visitor_timezone=r.visitor_timezone,
            visitor_local_date=self._date_label(at, v_tz) if at and v_tz else None,
            visitor_local_time=at.astimezone(v_tz).strftime("%I:%M %p").lstrip("0") if at and v_tz else None,
            created_at=r.created_at, updated_at=r.updated_at, deleted_at=r.deleted_at,
        )

    # ── 6. Export (CSV of the current filters, no paging) ────────────────────
    async def export_csv(self, q: SuperadminBookDemoListQuery, user: User,
                         ip: str | None = None, user_agent: str | None = None) -> tuple[str, str]:
        rows = await self.repo.fetch_all(self._filters(q, self._now()), q.order, EXPORT_LIMIT)
        buf = io.StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
        writer.writerow(EXPORT_FIELDS)
        for r in rows:
            writer.writerow([_csv_safe(getattr(r, f)) for f in EXPORT_FIELDS])

        await self.log_audit("superadmin_book_demo.export", "book_demo", None, user.id,
                             payload={"rows": len(rows), "view": q.view}, ip_address=ip, user_agent=user_agent)
        try:
            await self.session.commit()
        except Exception:  # noqa: BLE001  the audit row must never block a download
            await self.session.rollback()
            logger.exception("Book a Demo export audit failed - non-fatal")
        return f"book-a-demo-{self._today(self._now()):%Y%m%d}.csv", "﻿" + buf.getvalue()
