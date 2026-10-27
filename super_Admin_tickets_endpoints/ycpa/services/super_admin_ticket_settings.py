import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import BadRequestException, NotFoundException
from ycpa.models.ticket_support import CAPACITY, NEEDS_SA, TicketLevel, TicketTeamMember
from ycpa.repositories.super_admin_ticket_settings import SuperAdminTicketSettingsRepository
from ycpa.schemas.requests.super_admin_ticket_settings import (
    LevelCreateRequest,
    LevelSlaUpdateRequest,
    MemberCreateRequest,
    RulesUpdateRequest,
    TeamQuery,
)
from ycpa.schemas.responses.super_admin_ticket_settings import (
    LevelOut,
    MemberOut,
    SettingsRulesResponse,
    TeamResponse,
    TeamSummary,
    TicketSettingsResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


def next_level(status: str, level: int, max_level: int) -> int:
    return level if status == NEEDS_SA and level + 1 > max_level else level + 1


def _level_out(level: TicketLevel, member_count: int = 0) -> LevelOut:
    return LevelOut(
        id=level.id, name=level.name, description=level.description,
        sla_hours=level.sla_hours, member_count=member_count,
    )


class SuperAdminTicketSettingsService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SuperAdminTicketSettingsRepository(session)

    async def get_team(self, params: TeamQuery) -> TeamResponse:
        levels = await self.repo.levels()
        if params.level_id is not None and params.level_id not in {level.id for level, _ in levels}:
            raise NotFoundException("Level not found")
        rows, total = await self.repo.members_with_stats(
            params.level_id, params.q, params.sort,
            (params.page - 1) * params.per_page, params.per_page,
            member_id=params.member_id, name=params.name,
        )
        if params.member_id is not None and not total:
            raise NotFoundException("Team member not found")
        max_level = levels[-1][0].id if levels else 0
        waiting = sum(
            count for status, level_id, count in await self.repo.assignable_counts()
            if params.level_id is None or next_level(status, level_id, max_level) == params.level_id
        )
        members = sum(count for level, count in levels if params.level_id in (None, level.id))
        selected = next((level for level, _ in levels if level.id == params.level_id), None)
        return TeamResponse(
            levels=[_level_out(level, count) for level, count in levels],
            total_members=sum(count for _, count in levels),
            summary=TeamSummary(
                levels=len(levels) if selected is None else 1,
                members=members,
                active_tickets=await self.repo.active_total(params.level_id),
                waiting_for_assignment=waiting,
                sla_hours=selected.sla_hours if selected else None,
            ),
            items=[
                MemberOut(
                    id=member.id, name=member.name, level_id=member.level_id,
                    active=active, solved=solved, capacity=CAPACITY,
                    workload_pct=min(100.0, active / CAPACITY * 100),
                )
                for member, active, solved in rows
            ],
            total=total,
            page=params.page,
            per_page=params.per_page,
        )

    async def get_settings(self, params: TeamQuery) -> TicketSettingsResponse:
        team = await self.get_team(params)
        rules = await self.repo.get_rules()
        return TicketSettingsResponse(**team.model_dump(), rules=rules)

    async def create_level(self, body: LevelCreateRequest) -> LevelOut:
        level = await self.repo.create_level(TicketLevel(
            name=body.name, description=body.description or body.name, sla_hours=body.sla_hours,
        ))
        await self.session.commit()
        return _level_out(level)

    async def update_level_sla(self, level_id: int, body: LevelSlaUpdateRequest) -> LevelOut:
        level = await self.repo.get_level(level_id)
        if not level:
            raise NotFoundException("Level not found")
        # Applies to future assignments; existing deadlines remain unchanged.
        level.sla_hours = body.sla_hours
        await self.session.commit()
        return _level_out(level)

    async def create_member(self, body: MemberCreateRequest) -> MemberOut:
        if not await self.repo.get_level(body.level_id):
            raise BadRequestException("Invalid level")
        if body.user_id is not None and not await self.repo.user_exists(body.user_id):
            raise BadRequestException("Invalid or inactive user")
        member = await self.repo.create_member(TicketTeamMember(
            name=body.name, level_id=body.level_id, user_id=body.user_id,
        ))
        await self.session.commit()
        return MemberOut(
            id=member.id, name=member.name, level_id=member.level_id,
            active=0, solved=0, capacity=CAPACITY, workload_pct=0,
        )

    async def update_rules(self, body: RulesUpdateRequest) -> SettingsRulesResponse:
        values = body.model_dump(
            include={"auto_return", "notify_super_admin", "allow_skip_levels"},
            exclude_none=True,
        )
        if values:
            rules = await self.repo.update_rules(values)
            await self.session.commit()
        else:
            rules = await self.repo.get_rules()
        levels = await self.repo.levels()
        return SettingsRulesResponse(
            levels=[_level_out(level, count) for level, count in levels], rules=rules,
        )
