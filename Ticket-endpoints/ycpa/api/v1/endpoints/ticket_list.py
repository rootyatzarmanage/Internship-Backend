from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ycpa.core.auth.dependencies import StaffUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.ticket_list import TicketListQuery, ticket_list_query
from ycpa.schemas.responses.ticket_list import TicketListResponse, TicketStatsResponse
from ycpa.services.ticket_list import TicketListService

router = APIRouter(prefix="/ticket-list", tags=["Ticket List"])


@router.get("/stats", response_model=SuccessResponse[TicketStatsResponse], summary="Total / pending / solved counts")
async def ticket_stats(session: DatabaseSession, staff: StaffUser):
    return SuccessResponse(data=await TicketListService(session).stats())


@router.get("", response_model=SuccessResponse[TicketListResponse], summary="Support tickets table (All / Solved / Pending, search, sort)")
async def list_tickets(session: DatabaseSession, staff: StaffUser, q: Annotated[TicketListQuery, Depends(ticket_list_query)]):
    return SuccessResponse(data=await TicketListService(session).list_tickets(q))


@router.delete("/{ticket_id}", response_model=SuccessResponse[None], summary="Delete ticket (soft)")
async def delete_ticket(ticket_id: UUID, session: DatabaseSession, staff: StaffUser):
    await TicketListService(session).delete_ticket(ticket_id, staff)
    return SuccessResponse(message="Ticket deleted.")
