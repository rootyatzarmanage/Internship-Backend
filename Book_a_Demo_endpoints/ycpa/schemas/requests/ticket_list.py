from typing import Literal

from fastapi import Query
from pydantic import BaseModel


class TicketListQuery(BaseModel):
    status: Literal["all", "solved", "pending"] = "all"  # pending = everything not solved
    search: str | None = None
    category: str | None = None
    sort_by: Literal["created_at", "requested_by"] = "created_at"
    order: Literal["asc", "desc"] = "desc"
    page: int = 1
    per_page: int = 10


def ticket_list_query(
    status: Literal["all", "solved", "pending"] = Query("all"),
    search: str | None = Query(None, description="ticket id, subject, name or email"),
    category: str | None = Query(None),
    sort_by: Literal["created_at", "requested_by"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> TicketListQuery:
    return TicketListQuery(status=status, search=search, category=category, sort_by=sort_by, order=order, page=page, per_page=per_page)
