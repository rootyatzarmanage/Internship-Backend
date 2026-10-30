import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import ConflictException, DatabaseException, NotFoundException, ValidationException
from ycpa.models.book_demo_team import LEVEL, MEMBER, BookDemoTeam
from ycpa.models.user import User
from ycpa.repositories.superadmin_bookademo_team import (
    SuperadminBookDemoAssignmentRepository,
    SuperadminBookDemoLevelRepository,
    SuperadminBookDemoMemberRepository,
)
from ycpa.schemas.requests.superadmin_bookademo_team import (
    SuperadminBookDemoAssignmentRequest,
    SuperadminBookDemoLevelRequest,
    SuperadminBookDemoMemberRequest,
    SuperadminBookDemoTeamQuery,
)
from ycpa.schemas.responses.superadmin_bookademo_team import (
    AssignmentHistoryResponse,
    AssignmentMemberResponse,
    SuperadminBookDemoAssignmentResponse,
    SuperadminBookDemoTeamResponse,
    TeamLevelResponse,
    TeamMemberResponse,
    TeamStatsResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)

MAX_LEVELS = 30
MAX_MEMBERS = 500
SUMMARY_LIMIT = 3000
HISTORY_LIMIT = 60


class SuperadminBookDemoTeamService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.levels = SuperadminBookDemoLevelRepository(session)
        self.members = SuperadminBookDemoMemberRepository(session)
        self.assignments = SuperadminBookDemoAssignmentRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def _commit(self) -> None:
        """Commit the unit of work; a unique-index race surfaces as 409 instead of a 500."""
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictException("This change conflicts with an existing record", details={"error": str(e.orig)[:100]}) from e
        except DBAPIError as e:
            await self.session.rollback()
            logger.exception("Book a Demo team commit failed")
            raise DatabaseException("Failed to save the team changes") from e

    @staticmethod
    def _member(m: BookDemoTeam, level_name: str, assigned: int) -> TeamMemberResponse:
        return TeamMemberResponse(
            id=m.id, name=m.name, email=m.email, role=m.role, level_id=m.parent_id, level_name=level_name,
            is_active=m.is_active, assigned_bookings=assigned, created_at=m.created_at, updated_at=m.updated_at)

    async def _stats(self, levels: list[BookDemoTeam], members: list[BookDemoTeam]) -> TeamStatsResponse:
        cov = await self.members.coverage(self._now())
        active = sum(1 for m in members if m.is_active)
        return TeamStatsResponse(
            members=len(members), active_members=active, inactive_members=len(members) - active, levels=len(levels),
            assigned_bookings=cov["assigned"], needs_assignment=cov["needs_assignment"])

    async def overview(self, q: SuperadminBookDemoTeamQuery) -> SuperadminBookDemoTeamResponse:
        levels = await self.levels.list_all()
        members = await self.members.list_all()
        by_member, by_level = await self.members.workload()

        term = q.search.lower() if q.search else None

        def matches(*parts: str | None) -> bool:
            return term is None or term in " ".join(p or "" for p in parts).lower()

        items = []
        for lv in levels:
            own = [m for m in members if m.parent_id == lv.id]
            shown = [m for m in own if matches(lv.name, lv.description, m.name, m.email, m.role)]
            if term and not matches(lv.name, lv.description) and not shown:
                continue   
            items.append(TeamLevelResponse(
                id=lv.id, name=lv.name, description=lv.description, member_count=len(own),
                active_member_count=sum(1 for m in own if m.is_active), booking_count=by_level.get(lv.id, 0),
                members=[self._member(m, lv.name, by_member.get(m.id, 0)) for m in shown],
                created_at=lv.created_at, updated_at=lv.updated_at))
        return SuperadminBookDemoTeamResponse(stats=await self._stats(levels, members), levels=items)

    async def summary(self) -> TeamStatsResponse:
        """Stat cards, coverage grid and the "N upcoming demos need a team" strip - no member list."""
        return await self._stats(await self.levels.list_all(), await self.members.list_all())

    async def _level_response(self, level: BookDemoTeam) -> TeamLevelResponse:
        members = [m for m in await self.members.list_all() if m.parent_id == level.id]
        by_member, by_level = await self.members.workload()
        return TeamLevelResponse(
            id=level.id, name=level.name, description=level.description, member_count=len(members),
            active_member_count=sum(1 for m in members if m.is_active), booking_count=by_level.get(level.id, 0),
            members=[self._member(m, level.name, by_member.get(m.id, 0)) for m in members],
            created_at=level.created_at, updated_at=level.updated_at)

    async def create_level(self, body: SuperadminBookDemoLevelRequest, user: User,
                           ip: str | None = None, user_agent: str | None = None) -> TeamLevelResponse:
        if await self.levels.count_levels() >= MAX_LEVELS:
            raise ValidationException(f"You can create up to {MAX_LEVELS} levels.")
        if await self.levels.find_by_name(body.name):
            raise ConflictException("A level with this name already exists. Choose another name.", details={"name": body.name})
        level = await self.levels.create(BookDemoTeam(
            kind=LEVEL, name=body.name, description=body.description, created_by=user.id, updated_by=user.id))
        await self.log_audit("superadmin_book_demo.level.create", "book_demo_team_level", str(level.id), user.id,
                             changed_to={"name": level.name, "description": level.description},
                             ip_address=ip, user_agent=user_agent)
        await self._commit()
        return await self._level_response(level)

    async def update_level(self, level_id: UUID, body: SuperadminBookDemoLevelRequest, user: User,
                           ip: str | None = None, user_agent: str | None = None) -> TeamLevelResponse:
        level = await self.levels.get_level(level_id)
        if not level:
            raise NotFoundException("Level not found", resource="book_demo_team_level")
        if await self.levels.find_by_name(body.name, exclude_id=level_id):
            raise ConflictException("A level with this name already exists. Choose another name.", details={"name": body.name})
        before = {"name": level.name, "description": level.description}
        level = await self.levels.update_by_id(level_id, {"name": body.name, "description": body.description, "updated_by": user.id})
        await self.log_audit("superadmin_book_demo.level.update", "book_demo_team_level", str(level_id), user.id,
                             changed_from=before, changed_to={"name": body.name, "description": body.description},
                             ip_address=ip, user_agent=user_agent)
        await self._commit()
        return await self._level_response(level)

    async def delete_level(self, level_id: UUID, user: User, ip: str | None = None, user_agent: str | None = None) -> None:
        level = await self.levels.get_level(level_id)
        if not level:
            raise NotFoundException("Level not found", resource="book_demo_team_level")
        if await self.levels.count_levels() <= 1:
            raise ConflictException("Keep at least one level.")
        if await self.levels.member_count(level_id):
            raise ConflictException("Move all members out of this level before deleting it.")
        await self.levels.hard_delete(level_id)
        await self.log_audit("superadmin_book_demo.level.delete", "book_demo_team_level", str(level_id), user.id,
                             changed_from={"name": level.name, "description": level.description},
                             ip_address=ip, user_agent=user_agent)
        await self._commit()

    async def _member_response(self, member: BookDemoTeam) -> TeamMemberResponse:
        level = await self.levels.get_level(member.parent_id)
        by_member, _ = await self.members.workload()
        return self._member(member, level.name if level else "", by_member.get(member.id, 0))

    async def create_member(self, body: SuperadminBookDemoMemberRequest, user: User,
                            ip: str | None = None, user_agent: str | None = None) -> TeamMemberResponse:
        if await self.members.count_members() >= MAX_MEMBERS:
            raise ValidationException(f"You can add up to {MAX_MEMBERS} team members.")
        if not await self.levels.get_level(body.level_id):
            raise NotFoundException("Level not found", resource="book_demo_team_level")
        if await self.members.find_by_email(body.email):
            raise ConflictException("This work email is already used by a team member.", details={"email": body.email})
        member = await self.members.create(BookDemoTeam(
            kind=MEMBER, name=body.name, email=body.email, role=body.role, parent_id=body.level_id,
            is_active=body.is_active, created_by=user.id, updated_by=user.id))
        await self.log_audit("superadmin_book_demo.member.create", "book_demo_team_member", str(member.id), user.id,
                             changed_to={"name": member.name, "email": member.email, "role": member.role,
                                         "level_id": str(member.parent_id), "is_active": member.is_active},
                             ip_address=ip, user_agent=user_agent)
        await self._commit()
        return await self._member_response(member)

    async def update_member(self, member_id: UUID, body: SuperadminBookDemoMemberRequest, user: User,
                            ip: str | None = None, user_agent: str | None = None) -> TeamMemberResponse:
        member = await self.members.get_member(member_id)
        if not member:
            raise NotFoundException("Team member not found", resource="book_demo_team_member")
        if not await self.levels.get_level(body.level_id):
            raise NotFoundException("Level not found", resource="book_demo_team_level")
        if await self.members.find_by_email(body.email, exclude_id=member_id):
            raise ConflictException("This work email is already used by a team member.", details={"email": body.email})
        before = {"name": member.name, "email": member.email, "role": member.role,
                  "level_id": str(member.parent_id), "is_active": member.is_active}
        after = {"name": body.name, "email": body.email, "role": body.role,
                 "level_id": str(body.level_id), "is_active": body.is_active}
        member = await self.members.update_by_id(member_id, {
            "name": body.name, "email": body.email, "role": body.role, "parent_id": body.level_id,
            "is_active": body.is_active, "updated_by": user.id})
        await self.log_audit("superadmin_book_demo.member.update", "book_demo_team_member", str(member_id), user.id,
                             changed_from=before, changed_to=after, ip_address=ip, user_agent=user_agent)
        await self._commit()
        return await self._member_response(member)

    async def _assignment_response(self, booking) -> SuperadminBookDemoAssignmentResponse:
        ids = list(booking.assigned_member_ids or [])
        rows = await self.assignments.members_in_order(ids)
        primary = booking.assigned_primary_id if any(m.id == booking.assigned_primary_id for m, _ in rows) else None
        history = [AssignmentHistoryResponse(
            id=UUID(h["id"]), at=datetime.fromisoformat(h["at"]), summary=h["summary"], note=h.get("note"),
            actor_id=UUID(h["actor_id"]) if h.get("actor_id") else None, actor_name=h.get("actor_name"))
            for h in (booking.assignment_history or [])]
        return SuperadminBookDemoAssignmentResponse(
            booking_id=booking.id, book_demo_id=booking.book_demo_id, can_assign=booking.status != "cancelled",
            assigned=bool(rows), primary_member_id=primary,
            members=[AssignmentMemberResponse(
                member_id=m.id, name=m.name, email=m.email, role=m.role, level_id=lv.id, level_name=lv.name,
                is_active=m.is_active, is_primary=(m.id == primary)) for m, lv in rows],
            note=booking.assignment_note, history=history, updated_at=booking.assignment_updated_at)

    async def get_assignment(self, booking_id: UUID) -> SuperadminBookDemoAssignmentResponse:
        booking = await self.assignments.get_booking(booking_id)
        if not booking:
            raise NotFoundException("Booking not found", resource="book_demo")
        return await self._assignment_response(booking)

    async def save_assignment(self, booking_id: UUID, body: SuperadminBookDemoAssignmentRequest, user: User,
                              ip: str | None = None, user_agent: str | None = None) -> tuple[SuperadminBookDemoAssignmentResponse, bool]:
        """Replace the booking's team. Returns (assignment, changed); changed is False when nothing differs."""
        booking = await self.assignments.lock_booking(booking_id)
        if not booking:
            raise NotFoundException("Booking not found", resource="book_demo")
        if booking.status == "cancelled":
            raise ValidationException("This booking cannot receive an assignment.", details={"status": booking.status})

        old_ids = list(booking.assigned_member_ids or [])
        old_primary = booking.assigned_primary_id
        old_note = booking.assignment_note or ""

        found = {m.id: m for m in await self.members.get_many(body.member_ids)}
        missing = [str(i) for i in body.member_ids if i not in found]
        if missing:
            raise ValidationException("One or more team members do not exist.", details={"member_ids": missing})
        blocked = [str(i) for i in body.member_ids if not found[i].is_active and i not in old_ids]
        if blocked:   
            raise ValidationException("Choose active team members. An inactive member cannot receive a new assignment.",
                                      details={"member_ids": blocked})

        note = (body.note or "") if body.member_ids else ""
        if set(old_ids) == set(body.member_ids) and old_primary == body.primary_id and old_note == note:
            return await self._assignment_response(booking), False

        if body.member_ids:
            names = ", ".join(found[i].name + (" (primary)" if i == body.primary_id else "") for i in body.member_ids)
            summary = f"{'Team updated' if old_ids else 'Team assigned'}: {names}"
        else:
            summary = "Team assignment removed"

        now = self._now()
        entry = {"id": str(uuid.uuid4()), "at": now.isoformat(), "summary": summary[:SUMMARY_LIMIT],
                 "note": note or None, "actor_id": str(user.id), "actor_name": user.full_name}
        booking.assigned_member_ids = list(body.member_ids)
        booking.assigned_primary_id = body.primary_id
        booking.assignment_note = note or None
        booking.assignment_history = [entry, *(booking.assignment_history or [])][:HISTORY_LIMIT]   # new list so the change is tracked
        booking.assignment_updated_at = now
        booking.assignment_updated_by = user.id

        await self.log_audit("superadmin_book_demo.assignment.save", "book_demo", str(booking_id), user.id,
                             changed_from={"member_ids": [str(i) for i in old_ids], "primary_id": str(old_primary) if old_primary else None, "note": old_note},
                             changed_to={"member_ids": [str(i) for i in body.member_ids], "primary_id": str(body.primary_id) if body.primary_id else None, "note": note},
                             ip_address=ip, user_agent=user_agent)
        response = await self._assignment_response(booking)
        await self._commit()
        return response, True
