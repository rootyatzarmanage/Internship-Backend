import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ycpa.models.ticket_support import (
    CLOSED,
    ESCALATION,
    NEEDS_SA,
    ON_GOING,
    OPEN,
    RESOLVED,
    TRIAGE_SLA_H,
    TicketEvent,
    TicketTeamMember,
)
from ycpa.models.tickets import Ticket
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository
from ycpa.schemas.requests.super_admin_ticket_list import TicketListQuery

logger = logging.getLogger(__name__)

M = aliased(TicketTeamMember)
STATUS = case((Ticket.status == "pending", OPEN), else_=Ticket.status)
PRIORITY = Ticket.priority
LEVEL = Ticket.level_id
IS_ACTIVE = STATUS.in_([OPEN, ON_GOING, ESCALATION, NEEDS_SA])
DUE = case(
    (IS_ACTIVE, func.coalesce(Ticket.due_at, Ticket.created_at + timedelta(hours=TRIAGE_SLA_H))),
    else_=None,
)
PRI_RANK = case(
    (PRIORITY == "critical", 4),
    (PRIORITY == "high", 3),
    (PRIORITY == "medium", 2),
    else_=1,
)
TABS = {
    "all": None,
    "open": STATUS == OPEN,
    "esc": STATUS.in_([ESCALATION, NEEDS_SA]),
    "going": STATUS == ON_GOING,
    "done": STATUS.in_([RESOLVED, CLOSED]),
}


class SuperAdminTicketListRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    def _base(self):
        return (
            select(
                Ticket.id, Ticket.ticket_id, Ticket.ticket_no, Ticket.subject,
                Ticket.message, Ticket.category, Ticket.created_at,
                STATUS.label("status"), PRIORITY.label("priority"),
                LEVEL.label("level_id"), DUE.label("due_at"),
                Ticket.assignee_id, Ticket.resolved_at, Ticket.resolved_level,
                Ticket.resolved_by, M.name.label("assignee_name"),
                User.full_name.label("user_name"), User.email.label("user_email"),
            )
            .select_from(Ticket)
            .join(User, User.id == Ticket.user_id)
            .outerjoin(M, M.id == Ticket.assignee_id)
            .where(Ticket.deleted_at.is_(None))
        )

    def _filtered(self, p: TicketListQuery):
        query = self._base()
        if TABS[p.tab] is not None:
            query = query.where(TABS[p.tab])
        if p.id is not None:
            query = query.where(Ticket.id == p.id)
        if p.name and p.name.strip():
            name = f"%{p.name.strip()}%"
            query = query.where(or_(
                Ticket.subject.ilike(name), User.full_name.ilike(name), M.name.ilike(name),
            ))
        if p.q.strip():
            term = f"%{p.q.strip()}%"
            query = query.where(or_(
                Ticket.ticket_id.ilike(term), Ticket.subject.ilike(term),
                User.full_name.ilike(term), User.email.ilike(term),
                Ticket.category.ilike(term), M.name.ilike(term),
            ))
        if p.date_from:
            query = query.where(Ticket.created_at >= datetime.combine(p.date_from, time.min, timezone.utc))
        if p.date_to:
            query = query.where(Ticket.created_at <= datetime.combine(p.date_to, time.max, timezone.utc))
        if p.status:
            query = query.where(STATUS == p.status)
        if p.priority:
            query = query.where(PRIORITY == p.priority)
        if p.level_id is not None:
            query = query.where(LEVEL == p.level_id)
        if p.category:
            query = query.where(Ticket.category == p.category)
        return query

    async def list_page(self, p: TicketListQuery, offset: int = 0, limit: int | None = None):
        query = self._filtered(p)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        order = {
            "old": [Ticket.created_at.asc()],
            "pri": [PRI_RANK.desc(), Ticket.created_at.desc()],
            "sla": [DUE.asc().nulls_last(), Ticket.created_at.desc()],
        }.get(p.sort, [Ticket.created_at.desc()])
        result = await self.session.execute(
            query.order_by(*order, Ticket.id).offset(offset).limit(limit)
        )
        return result.all(), total or 0

    async def tab_counts(self) -> dict[str, int]:
        columns = [
            (func.count() if condition is None else func.count().filter(condition)).label(name)
            for name, condition in TABS.items()
        ]
        result = await self.session.execute(
            select(*columns).select_from(Ticket).where(Ticket.deleted_at.is_(None))
        )
        return dict(result.one()._mapping)

    async def get_row(self, ticket_id: UUID, lock: bool = False):
        query = self._base().where(Ticket.id == ticket_id)
        if lock:
            query = query.with_for_update(of=Ticket)
        return (await self.session.execute(query)).one_or_none()

    async def events(self, ticket_id: UUID) -> list[TicketEvent]:
        result = await self.session.execute(
            select(TicketEvent)
            .where(TicketEvent.ticket_id == ticket_id)
            .order_by(TicketEvent.created_at, TicketEvent.id)
        )
        return list(result.scalars().all())

    async def categories(self) -> list[str]:
        result = await self.session.execute(
            select(Ticket.category)
            .where(Ticket.deleted_at.is_(None))
            .distinct()
            .order_by(Ticket.category)
        )
        return list(result.scalars().all())

    async def users(self, limit: int = 200):
        result = await self.session.execute(
            select(User.id, User.full_name, User.email)
            .where(User.deleted_at.is_(None), User.is_active.is_(True), User.platform_role == "customer")
            .order_by(User.full_name, User.id)
            .limit(limit)
        )
        return result.all()

    async def get_user(self, user_id: UUID):
        result = await self.session.execute(
            select(User.id, User.full_name)
            .where(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True))
        )
        return result.one_or_none()

    async def breached_ongoing(self, now: datetime) -> list[UUID]:
        result = await self.session.execute(
            select(Ticket.id)
            .where(Ticket.deleted_at.is_(None), Ticket.status == ON_GOING, Ticket.due_at < now)
            .order_by(Ticket.id)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def create_ticket(self, ticket: Ticket) -> Ticket:
        return await self.create(ticket)

    async def update_ticket(self, ticket_id: UUID, **values: Any) -> None:
        await self.session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
            .values(**values, updated_at=datetime.now(timezone.utc))
        )

    def add_event(self, ticket_id: UUID, type_: str, text: str, by: str, level_id: int = 0) -> None:
        self.session.add(TicketEvent(
            ticket_id=ticket_id, type=type_, text=text, by_name=by, level_id=level_id,
        ))
