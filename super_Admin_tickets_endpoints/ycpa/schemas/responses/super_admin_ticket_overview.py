from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    total: int
    today: int = Field(description="Tickets created within the last 24 hours, matching the reference dashboard.")
    awaiting_assignment: int
    escalation_queue: int
    resolved_closed: int
    resolution_rate: int = Field(description="Resolved/closed percentage, rounded to the nearest integer with halves rounded up.")
    sla_breached: int
    nav_count: int 


class StatusSlice(BaseModel):
    status: str
    label: str
    count: int


class LevelSeries(BaseModel):
    level_id: int  
    label: str
    counts: list[int]  
    
class ResolvedByLevel(BaseModel):
    months: list[str]
    series: list[LevelSeries]


class AttentionItem(BaseModel):
    id: UUID
    ticket_id: str | None
    subject: str
    status: str
    status_label: str
    sla_text: str
    sla_state: str
    due_at: datetime | None


class TicketOverviewResponse(BaseModel):
    stats: OverviewStats
    status_breakdown: list[StatusSlice]
    resolved_by_level: ResolvedByLevel
    needs_attention: list[AttentionItem]
