import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.control_panel import ControlPanel
from ycpa.models.ticket_support import (
    ASSIGNABLE,
    CLOSED,
    ON_GOING,
    RESOLVED,
    TicketLevel,
    TicketTeamMember,
)
from ycpa.models.tickets import Ticket
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository
from ycpa.schemas.responses.super_admin_ticket_settings import RulesOut

logger = logging.getLogger(__name__)
RULES_SLUG = "Ticket Settings/Escalation Rules"


class SuperAdminTicketSettingsRepository(BaseRepository[TicketTeamMember]):
    def __init__(self, session: AsyncSession):
        super().__init__(TicketTeamMember, session)

    async def levels(self) -> list[tuple[TicketLevel, int]]:
        counts = (
            select(TicketTeamMember.level_id, func.count().label("members"))
            .where(TicketTeamMember.is_active.is_(True))
            .group_by(TicketTeamMember.level_id)
            .subquery()
        )
        result = await self.session.execute(
            select(TicketLevel, func.coalesce(counts.c.members, 0))
            .outerjoin(counts, counts.c.level_id == TicketLevel.id)
            .order_by(TicketLevel.id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_level(self, level_id: int) -> TicketLevel | None:
        return await self.session.get(TicketLevel, level_id)

    async def create_level(self, level: TicketLevel) -> TicketLevel:
        self.session.add(level)
        await self.session.flush()
        return level

    async def get_member(self, member_id: UUID) -> TicketTeamMember | None:
        return await self.get_by_id(member_id)

    async def create_member(self, member: TicketTeamMember) -> TicketTeamMember:
        return await self.create(member)

    async def user_exists(self, user_id: UUID) -> bool:
        return bool(await self.session.scalar(
            select(User.id)
            .where(User.id == user_id, User.is_active.is_(True), User.deleted_at.is_(None))
        ))

    async def members_with_stats(
        self, level_id=None, q="", sort="name", offset=0, limit=8,
        member_id=None, name=None,
    ):
        active = (
            select(Ticket.assignee_id.label("member_id"), func.count().label("count"))
            .where(Ticket.status == ON_GOING, Ticket.deleted_at.is_(None))
            .group_by(Ticket.assignee_id)
            .subquery()
        )
        solved = (
            select(Ticket.resolved_by.label("member_id"), func.count().label("count"))
            .where(Ticket.status.in_([RESOLVED, CLOSED]), Ticket.deleted_at.is_(None))
            .group_by(Ticket.resolved_by)
            .subquery()
        )
        active_count = func.coalesce(active.c.count, 0)
        solved_count = func.coalesce(solved.c.count, 0)
        where = [TicketTeamMember.is_active.is_(True)]
        if level_id is not None:
            where.append(TicketTeamMember.level_id == level_id)
        if member_id is not None:
            where.append(TicketTeamMember.id == member_id)
        for term in (q, name):
            if term and term.strip():
                where.append(TicketTeamMember.name.ilike(f"%{term.strip()}%"))
        order = {
            "active": active_count.desc(), "free": active_count.asc(),
            "solved": solved_count.desc(),
        }.get(sort, TicketTeamMember.name.asc())
        total = await self.session.scalar(
            select(func.count()).select_from(TicketTeamMember).where(*where)
        )
        result = await self.session.execute(
            select(TicketTeamMember, active_count.label("active"), solved_count.label("solved"))
            .outerjoin(active, active.c.member_id == TicketTeamMember.id)
            .outerjoin(solved, solved.c.member_id == TicketTeamMember.id)
            .where(*where)
            .order_by(order, TicketTeamMember.name, TicketTeamMember.id)
            .offset(offset)
            .limit(limit)
        )
        return result.all(), total or 0

    async def active_total(self, level_id=None) -> int:
        query = select(func.count()).select_from(Ticket).where(
            Ticket.status == ON_GOING, Ticket.deleted_at.is_(None),
        )
        if level_id is not None:
            query = query.where(Ticket.level_id == level_id)
        return await self.session.scalar(query) or 0

    async def assignable_counts(self) -> list[tuple[str, int, int]]:
        result = await self.session.execute(
            select(Ticket.status, Ticket.level_id, func.count())
            .where(Ticket.deleted_at.is_(None), Ticket.status.in_(ASSIGNABLE))
            .group_by(Ticket.status, Ticket.level_id)
        )
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def get_rules(self) -> RulesOut:
        values = await self.session.scalar(
            select(ControlPanel.value_json)
            .where(ControlPanel.slug == RULES_SLUG, ControlPanel.deleted_at.is_(None))
        )
        return RulesOut.model_validate(values or {})

    async def update_rules(self, values: dict) -> RulesOut:
        now = datetime.now(timezone.utc)
        defaults = RulesOut().model_dump()
        statement = insert(ControlPanel).values(
            id=uuid4(), slug=RULES_SLUG, name="Ticket escalation rules", fieldtype=2,
            value_json={**defaults, **values}, created_at=now, updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ControlPanel.slug],
            set_={
                "value_json": func.coalesce(ControlPanel.value_json, cast(defaults, JSONB)).op("||")(cast(values, JSONB)),
                "updated_at": now,
                "deleted_at": None,
            },
        ).returning(ControlPanel.value_json)
        result = await self.session.scalar(statement)
        return RulesOut.model_validate(result)
