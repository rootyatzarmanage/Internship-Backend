from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AssigneeOut(BaseModel):
    id: UUID
    name: str


class TicketListItem(BaseModel):
    id: UUID
    ticket_id: str | None
    ticket_no: int
    subject: str
    user_name: str
    user_email: str
    category: str
    priority: str
    level_id: int  
    assignee: AssigneeOut | None = None
    status: str
    status_label: str
    next_level: int | None = None 
    sla_text: str
    sla_state: str 
    due_at: datetime | None = None
    created_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    per_page: int
    tab_counts: dict[str, int]


class MemberOption(BaseModel):
    id: UUID
    name: str
    level_id: int
    active: int


class LevelOption(BaseModel):
    id: int
    name: str
    sla_hours: int
    members: list[MemberOption]


class UserOption(BaseModel):
    id: UUID
    full_name: str
    email: str


class TicketListOptions(BaseModel):
    categories: list[str]
    levels: list[LevelOption]
    users: list[UserOption]
    allow_skip_levels: bool


class EventOut(BaseModel):
    id: UUID
    type: str
    text: str
    by: str
    level_id: int
    at: datetime


class PathStep(BaseModel):
    level_id: int  
    name: str
    state: str  
    note: str


class TicketDetail(TicketListItem):
    message: str
    level_name: str | None = None
    can_assign: bool
    path: list[PathStep]
    history: list[EventOut]
    notes: list[EventOut]


class BulkAssignResult(BaseModel):
    assigned: int
    skipped: int
    errors: list[str]


class SlaSweepResult(BaseModel):
    returned: int
