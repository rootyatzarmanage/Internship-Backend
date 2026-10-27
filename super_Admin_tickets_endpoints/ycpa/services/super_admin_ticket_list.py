import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import BadRequestException, NotFoundException
from ycpa.models.ticket_support import (
    CLOSED,
    ESCALATION,
    NEEDS_SA,
    ON_GOING,
    OPEN,
    RESOLVED,
    TRIAGE_SLA_H,
)
from ycpa.models.tickets import Ticket
from ycpa.models.user import User
from ycpa.repositories.super_admin_ticket_list import SuperAdminTicketListRepository
from ycpa.repositories.super_admin_ticket_settings import SuperAdminTicketSettingsRepository
from ycpa.schemas.requests.super_admin_ticket_list import (
    BulkAssignRequest,
    PriorityUpdateRequest,
    TicketActionRequest,
    TicketCreateRequest,
    TicketListQuery,
)
from ycpa.schemas.requests.super_admin_ticket_overview import OverviewQuery
from ycpa.schemas.responses.super_admin_ticket_list import (
    AssigneeOut,
    BulkAssignResult,
    EventOut,
    LevelOption,
    MemberOption,
    PathStep,
    SlaSweepResult,
    TicketDetail,
    TicketListItem,
    TicketListOptions,
    TicketListResponse,
    UserOption,
)
from ycpa.services.base import BaseService
from ycpa.services.super_admin_ticket_settings import next_level

logger = logging.getLogger(__name__)

STATUS_LABEL = {
    OPEN: "Open",
    ON_GOING: "On going",
    ESCALATION: "Escalation Pending",
    NEEDS_SA: "Needs Super Admin",
    RESOLVED: "Resolved",
    CLOSED: "Closed",
}
ACTIVE_STATES = (OPEN, ON_GOING, ESCALATION, NEEDS_SA)
ASSIGNABLE_STATES = (OPEN, ESCALATION, NEEDS_SA)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sla_info(status: str, due_at: datetime | None, now: datetime) -> tuple[str, str]:
    if status not in ACTIVE_STATES or not due_at:
        return "-", "none"
    seconds = int((due_at - now).total_seconds())
    if seconds < 0:
        return "Breached", "breached"
    text = f"{seconds // 3600}h {seconds % 3600 // 60}m left"
    return text, "warn" if seconds < 3600 else "ok"


class SuperAdminTicketListService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SuperAdminTicketListRepository(session)
        self.cfg = SuperAdminTicketSettingsRepository(session)

    async def read(self, params: TicketListQuery):
        if params.id is not None:
            if params.view != "list":
                raise BadRequestException("ID lookup cannot be combined with another view")
            return await self.detail(params.id)
        if params.view == "overview":
            from ycpa.services.super_admin_ticket_overview import SuperAdminTicketOverviewService

            return await SuperAdminTicketOverviewService(self.session).get_overview(
                OverviewQuery(months=params.months, attention_limit=params.attention_limit)
            )
        if params.view == "options":
            return await self.options()
        if params.view == "export":
            return await self.export_csv(params)
        return await self.list_tickets(params)

    async def apply_action(self, body: TicketActionRequest, admin: User):
        if body.action == "sweep_sla":
            return SlaSweepResult(returned=await self.sweep_sla()), "SLA sweep completed."
        if body.action == "bulk_assign":
            return await self.bulk_assign(body, admin), "Bulk assignment completed."
        if body.action == "assign":
            return await self.assign(body.ticket_id, body.member_id, admin), "Ticket assigned."
        if body.action == "cant_resolve":
            data, notify = await self.cant_resolve(body.ticket_id, body.reason, admin)
            message = (
                f"Escalation alert: {data.ticket_id} needs reassignment."
                if notify else "Returned to Super Admin."
            )
            return data, message
        if body.action in ("resolve", "team_resolve"):
            data = await self.resolve(body.ticket_id, body.action == "team_resolve", admin)
            return data, "Ticket resolved."
        if body.action == "close":
            return await self.close(body.ticket_id, admin), "Ticket closed."
        if body.action == "reopen":
            return await self.reopen(body.ticket_id, admin), "Ticket reopened."
        if body.action == "priority":
            return await self.set_priority(body.ticket_id, body, admin), "Priority updated."
        if body.action == "note":
            return await self.add_note(body.ticket_id, body.text, admin), "Note added."
        raise BadRequestException("Unsupported ticket action")

    async def _max_level(self) -> int:
        levels = await self.cfg.levels()
        return levels[-1][0].id if levels else 0

    def _item(self, row, max_level: int, now: datetime) -> dict:
        text, state = sla_info(row.status, row.due_at, now)
        can_assign = row.status in ASSIGNABLE_STATES
        return {
            "id": row.id,
            "ticket_id": row.ticket_id,
            "ticket_no": row.ticket_no,
            "subject": row.subject,
            "user_name": row.user_name,
            "user_email": row.user_email,
            "category": row.category,
            "priority": row.priority,
            "level_id": row.level_id,
            "assignee": AssigneeOut(id=row.assignee_id, name=row.assignee_name) if row.assignee_id else None,
            "status": row.status,
            "status_label": STATUS_LABEL.get(row.status, row.status),
            "next_level": next_level(row.status, row.level_id, max_level) if can_assign else None,
            "sla_text": text,
            "sla_state": state,
            "due_at": row.due_at,
            "created_at": row.created_at,
        }

    async def list_tickets(self, params: TicketListQuery) -> TicketListResponse:
        rows, total = await self.repo.list_page(
            params, (params.page - 1) * params.per_page, params.per_page,
        )
        max_level, now = await self._max_level(), now_utc()
        return TicketListResponse(
            items=[TicketListItem(**self._item(row, max_level, now)) for row in rows],
            total=total,
            page=params.page,
            per_page=params.per_page,
            tab_counts=await self.repo.tab_counts(),
        )

    async def options(self) -> TicketListOptions:
        levels = await self.cfg.levels()
        members, _ = await self.cfg.members_with_stats(limit=None)
        rules = await self.cfg.get_rules()
        by_level = {}
        for member, active, _ in members:
            by_level.setdefault(member.level_id, []).append(MemberOption(
                id=member.id, name=member.name, level_id=member.level_id, active=active,
            ))
        return TicketListOptions(
            categories=await self.repo.categories(),
            levels=[
                LevelOption(
                    id=level.id, name=level.name, sla_hours=level.sla_hours,
                    members=by_level.get(level.id, []),
                )
                for level, _ in levels
            ],
            users=[
                UserOption(id=user.id, full_name=user.full_name, email=user.email)
                for user in await self.repo.users()
            ],
            allow_skip_levels=rules.allow_skip_levels,
        )

    async def detail(self, ticket_id: UUID) -> TicketDetail:
        row = await self._state(ticket_id)
        levels = await self.cfg.levels()
        max_level = levels[-1][0].id if levels else 0
        events = await self.repo.events(ticket_id)
        failed = {event.level_id for event in events if event.type == "failed"}
        active = row.status in ACTIVE_STATES
        path = []
        for level, _ in levels:
            state, note = "pending", "Pending"
            if level.id in failed:
                state, note = "failed", "Could not resolve"
            if row.level_id == level.id and row.status == ON_GOING:
                state, note = "current", "Working: " + (row.assignee_name or "")
            if row.resolved_level == level.id and not active:
                state, note = "done", "Resolved"
            path.append(PathStep(level_id=level.id, name=level.name, state=state, note=note))
        admin_done = row.resolved_level == 0 and not active
        path.append(PathStep(
            level_id=0,
            name="Super Admin",
            state="current" if row.status == NEEDS_SA else "done" if admin_done else "standby",
            note="Action needed" if row.status == NEEDS_SA else "Resolved" if admin_done else "Standby",
        ))
        level = next((level for level, _ in levels if level.id == row.level_id), None)
        history, notes = [], []
        for event in events:
            output = EventOut(
                id=event.id, type=event.type, text=event.text,
                by=event.by_name, level_id=event.level_id, at=event.created_at,
            )
            (notes if event.type == "note" else history).append(output)
        return TicketDetail(
            **self._item(row, max_level, now_utc()),
            message=row.message,
            level_name=level.name if level else None,
            can_assign=row.status in ASSIGNABLE_STATES,
            path=path,
            history=history,
            notes=notes,
        )

    async def export_csv(self, params: TicketListQuery) -> str:
        rows, _ = await self.repo.list_page(params)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "Ticket ID", "Subject", "User", "Email", "Category", "Priority",
            "Level", "Assigned To", "Status", "Created",
        ])
        for row in rows:
            cells = [
                row.ticket_id, row.subject, row.user_name, row.user_email, row.category,
                row.priority, row.level_id or "", row.assignee_name or "",
                STATUS_LABEL.get(row.status, row.status), row.created_at.isoformat(),
            ]
            writer.writerow([
                "'" + value
                if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r"))
                else value
                for value in cells
            ])
        return buffer.getvalue()

    async def create(self, body: TicketCreateRequest, admin: User) -> TicketDetail:
        user = await self.repo.get_user(body.user_id)
        if not user:
            raise NotFoundException("User not found")
        ticket = await self.repo.create_ticket(Ticket(
            user_id=user.id,
            category=body.category,
            subject=body.subject,
            message=body.description,
            status=OPEN,
            updated_by=admin.id,
            priority=body.priority,
            level_id=0,
            due_at=now_utc() + timedelta(hours=TRIAGE_SLA_H),
        ))
        self.repo.add_event(
            ticket.id, "received", "Ticket received. Waiting for Super Admin to assign to Level 1.", user.full_name,
        )
        await self.session.commit()
        return await self.detail(ticket.id)

    async def assign(self, ticket_id: UUID, member_id: UUID, admin: User) -> TicketDetail:
        await self._assign(ticket_id, member_id, admin)
        await self.session.commit()
        return await self.detail(ticket_id)

    async def bulk_assign(self, body: BulkAssignRequest, admin: User) -> BulkAssignResult:
        context = (
            await self.cfg.get_member(body.member_id),
            await self.cfg.levels(),
            await self.cfg.get_rules(),
        )
        assigned, errors = 0, []
        for ticket_id in sorted(body.ticket_ids):
            try:
                async with self.session.begin_nested():
                    await self._assign(ticket_id, body.member_id, admin, context=context)
                assigned += 1
            except (BadRequestException, NotFoundException) as exc:
                errors.append(exc.message)
        await self.session.commit()
        return BulkAssignResult(assigned=assigned, skipped=len(errors), errors=errors)

    async def cant_resolve(self, ticket_id: UUID, reason: str | None, admin: User) -> tuple[TicketDetail, bool]:
        await self._cant_resolve(ticket_id, reason or "Needs deeper investigation", admin.id, admin.full_name)
        notify = (await self.cfg.get_rules()).notify_super_admin
        await self.session.commit()
        return await self.detail(ticket_id), notify

    async def resolve(self, ticket_id: UUID, via_team: bool, admin: User) -> TicketDetail:
        row = await self._state(ticket_id, lock=True)
        if row.status in (RESOLVED, CLOSED):
            raise BadRequestException("Ticket already finished.")
        values = {"resolved_at": now_utc(), "due_at": None, "resolved_level": 0, "resolved_by": None}
        if via_team and row.assignee_id:
            values.update(resolved_level=row.level_id, resolved_by=row.assignee_id)
            text, author = f"Resolved by {row.assignee_name} (Level {row.level_id}).", row.assignee_name
        else:
            values["assignee_id"] = None
            text, author = "Resolved by Super Admin.", admin.full_name
        await self.repo.update_ticket(ticket_id, status=RESOLVED, updated_by=admin.id, **values)
        self.repo.add_event(ticket_id, "resolved", text, author, values["resolved_level"])
        await self.session.commit()
        return await self.detail(ticket_id)

    async def close(self, ticket_id: UUID, admin: User) -> TicketDetail:
        row = await self._state(ticket_id, lock=True)
        values = {"due_at": None}
        if row.status != RESOLVED:
            values.update(
                resolved_at=row.resolved_at or now_utc(),
                resolved_level=row.resolved_level if row.resolved_level is not None else 0,
            )
        await self.repo.update_ticket(ticket_id, status=CLOSED, updated_by=admin.id, **values)
        self.repo.add_event(ticket_id, "closed", "Ticket closed by Super Admin.", admin.full_name)
        await self.session.commit()
        return await self.detail(ticket_id)

    async def reopen(self, ticket_id: UUID, admin: User) -> TicketDetail:
        await self._state(ticket_id, lock=True)
        await self.repo.update_ticket(
            ticket_id, status=OPEN, updated_by=admin.id,
            level_id=0, assignee_id=None, assigned_at=None,
            resolved_at=None, resolved_level=None, resolved_by=None,
            due_at=now_utc() + timedelta(hours=TRIAGE_SLA_H),
        )
        self.repo.add_event(ticket_id, "received", "Ticket reopened. Hierarchy restarted from Level 1.", admin.full_name)
        await self.session.commit()
        return await self.detail(ticket_id)

    async def set_priority(self, ticket_id: UUID, body: PriorityUpdateRequest, admin: User) -> TicketDetail:
        row = await self._state(ticket_id, lock=True)
        await self.repo.update_ticket(ticket_id, priority=body.priority, updated_by=admin.id)
        self.repo.add_event(ticket_id, "priority", f"Priority changed {row.priority} to {body.priority}.", admin.full_name)
        await self.session.commit()
        return await self.detail(ticket_id)

    async def add_note(self, ticket_id: UUID, text: str, admin: User) -> TicketDetail:
        await self._state(ticket_id, lock=True)
        self.repo.add_event(ticket_id, "note", text.strip(), admin.full_name)
        await self.session.commit()
        return await self.detail(ticket_id)

    async def sweep_sla(self) -> int:
        if not (await self.cfg.get_rules()).auto_return:
            return 0
        ids = await self.repo.breached_ongoing(now_utc())
        if ids:
            max_level = await self._max_level()
            for ticket_id in ids:
                await self._cant_resolve(
                    ticket_id, "SLA breached (auto-flagged)", None, "System", max_level=max_level,
                )
            await self.session.commit()
        return len(ids)

    async def _state(self, ticket_id: UUID, lock: bool = False):
        row = await self.repo.get_row(ticket_id, lock=lock)
        if not row:
            raise NotFoundException("Ticket not found")
        return row

    async def _assign(self, ticket_id: UUID, member_id: UUID, admin: User, context=None) -> None:
        row = await self._state(ticket_id, lock=True)
        if row.status not in ASSIGNABLE_STATES:
            raise BadRequestException(f"{row.ticket_id} cannot be assigned in its current state.")
        member, levels, rules = context if context is not None else (
            await self.cfg.get_member(member_id), await self.cfg.levels(), await self.cfg.get_rules(),
        )
        if not member or not member.is_active:
            raise NotFoundException("Team member not found")
        max_level = levels[-1][0].id if levels else 0
        target = next_level(row.status, row.level_id, max_level)
        if not rules.allow_skip_levels and member.level_id != target:
            raise BadRequestException(f"Hierarchy rule: {row.ticket_id} must be assigned to Level {target} next.")
        level = next((level for level, _ in levels if level.id == member.level_id), None)
        if not level:
            raise NotFoundException("Level not found")
        now = now_utc()
        await self.repo.update_ticket(
            ticket_id, status=ON_GOING, updated_by=admin.id,
            level_id=member.level_id, assignee_id=member.id,
            assigned_at=now, due_at=now + timedelta(hours=level.sla_hours),
        )
        self.repo.add_event(
            ticket_id, "assigned", f"Assigned to {member.name} (Level {member.level_id} - {level.name}).",
            admin.full_name, member.level_id,
        )

    async def _cant_resolve(
        self, ticket_id: UUID, reason: str, author_id: UUID | None, author_name: str,
        max_level: int | None = None,
    ) -> None:
        row = await self._state(ticket_id, lock=True)
        if row.status != ON_GOING:
            raise BadRequestException("Only on-going tickets can be returned.")
        if max_level is None:
            max_level = await self._max_level()
        last = row.level_id >= max_level
        await self.repo.update_ticket(
            ticket_id, status=NEEDS_SA if last else ESCALATION, updated_by=author_id,
            assignee_id=None, due_at=now_utc() + timedelta(hours=TRIAGE_SLA_H),
        )
        tail = (
            "Returned to Super Admin for final handling." if last
            else f"Returned to Super Admin for assignment to Level {row.level_id + 1}."
        )
        self.repo.add_event(
            ticket_id, "failed",
            f"Level {row.level_id} ({row.assignee_name or 'team'}) could not resolve: {reason}. {tail}",
            author_name, row.level_id,
        )
