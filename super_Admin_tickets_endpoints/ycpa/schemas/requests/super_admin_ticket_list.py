from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Priority = Literal["low", "medium", "high", "critical"]


class TicketListQuery(BaseModel):
    id: UUID | None = None
    name: str | None = None
    view: Literal["list", "overview", "options", "export"] = Field(
        "list",
        description="Use overview for KPI cards, status breakdown, resolved-by-level chart, and needs-attention tickets; options for dropdowns; export for CSV.",
    )
    tab: Literal["all", "open", "esc", "going", "done"] = "all"
    q: str = ""
    date_from: date | None = None
    date_to: date | None = None
    status: Literal[
        "open", "on_going", "escalation_pending", "needs_super_admin", "resolved", "closed"
    ] | None = None
    priority: Priority | None = None
    level_id: int | None = Field(None, ge=0)
    category: str | None = None
    sort: Literal["new", "old", "pri", "sla"] = "new"
    page: int = Field(1, ge=1)
    per_page: int = Field(6, ge=1, le=100)
    months: int = Field(6, ge=1, le=12)
    attention_limit: int = Field(6, ge=1, le=20)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        return self


class TicketCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject: str = Field(..., min_length=1, max_length=255)
    user_id: UUID
    category: str = Field(..., min_length=1)
    priority: Priority = "medium"
    description: str = ""


class BulkAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    member_id: UUID

    @model_validator(mode="after")
    def unique_tickets(self):
        self.ticket_ids = list(dict.fromkeys(self.ticket_ids))
        return self


class PriorityUpdateRequest(BaseModel):
    priority: Priority


class TicketAction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticket_id: UUID


class AssignAction(TicketAction):
    action: Literal["assign"]
    member_id: UUID


class BulkAssignAction(BulkAssignRequest):
    action: Literal["bulk_assign"]


class CantResolveAction(TicketAction):
    action: Literal["cant_resolve"]
    reason: str | None = Field(None, max_length=500)


class TeamResolveAction(TicketAction):
    action: Literal["team_resolve"]


class ResolveAction(TicketAction):
    action: Literal["resolve"]


class CloseAction(TicketAction):
    action: Literal["close"]


class ReopenAction(TicketAction):
    action: Literal["reopen"]


class PriorityAction(TicketAction):
    action: Literal["priority"]
    priority: Priority


class NoteAction(TicketAction):
    action: Literal["note"]
    text: str = Field(..., min_length=1, max_length=2000)


class SweepSlaAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["sweep_sla"]


TicketActionRequest = Annotated[
    AssignAction | BulkAssignAction | CantResolveAction | TeamResolveAction
    | ResolveAction | CloseAction | ReopenAction | PriorityAction | NoteAction | SweepSlaAction,
    Field(discriminator="action"),
]
