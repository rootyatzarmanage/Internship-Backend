from typing import Annotated

from fastapi import APIRouter, Depends

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.ticket_list import TicketListQuery, ticket_list_query
from ycpa.schemas.responses.ticket_list import TicketListResponse, TicketStatsResponse
from ycpa.services.ticket_list import TicketListService

router = APIRouter(prefix="/ticket-list", tags=["Ticket List"])


@router.get("/stats", response_model=SuccessResponse[TicketStatsResponse], summary="Total / pending / solved counts")
async def ticket_stats(session: DatabaseSession, current_user: CurrentUser):
    return SuccessResponse(data=await TicketListService(session).stats(current_user))


@router.get("", response_model=SuccessResponse[TicketListResponse], summary="Support tickets table (All / Solved / Pending, search, sort)")
async def list_tickets(session: DatabaseSession, current_user: CurrentUser, q: Annotated[TicketListQuery, Depends(ticket_list_query)]):
    return SuccessResponse(data=await TicketListService(session).list_tickets(current_user, q))
