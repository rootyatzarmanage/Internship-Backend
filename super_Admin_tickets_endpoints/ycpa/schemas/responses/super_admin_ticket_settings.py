from uuid import UUID

from pydantic import BaseModel


class LevelOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    sla_hours: int
    member_count: int = 0


class MemberOut(BaseModel):
    id: UUID
    name: str
    level_id: int
    active: int
    solved: int
    capacity: int
    workload_pct: float


class TeamSummary(BaseModel):
    levels: int
    members: int
    active_tickets: int
    waiting_for_assignment: int
    sla_hours: int | None = None  


class TeamResponse(BaseModel):
    levels: list[LevelOut]  
    total_members: int
    summary: TeamSummary
    items: list[MemberOut]
    total: int
    page: int
    per_page: int


class RulesOut(BaseModel):
    auto_return: bool = True
    notify_super_admin: bool = True
    allow_skip_levels: bool = False


class SettingsRulesResponse(BaseModel):
    levels: list[LevelOut]  
    rules: RulesOut


class TicketSettingsResponse(TeamResponse):
    rules: RulesOut
