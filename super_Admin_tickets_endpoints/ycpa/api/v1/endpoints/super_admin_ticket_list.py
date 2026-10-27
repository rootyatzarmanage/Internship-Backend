import logging
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.super_admin_ticket_list import (
    TicketActionRequest,
    TicketCreateRequest,
    TicketListQuery,
)
from ycpa.schemas.responses.super_admin_ticket_list import (
    BulkAssignResult,
    SlaSweepResult,
    TicketDetail,
    TicketListOptions,
    TicketListResponse,
)
from ycpa.schemas.responses.super_admin_ticket_overview import TicketOverviewResponse
from ycpa.services.super_admin_ticket_list import SuperAdminTicketListService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/super-admin/tickets",
    tags=["Super Admin - Tickets"],
)


@router.get(
    "",
    response_model=SuccessResponse[
        TicketListResponse | TicketDetail | TicketOverviewResponse | TicketListOptions
    ],
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
    summary="List/search tickets or read overview KPIs, charts, options, and export",
)
async def get_tickets(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    params: Annotated[TicketListQuery, Query()],
):
    service = SuperAdminTicketListService(session)
    data = await service.read(params)
    if params.view == "export":
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="tickets.csv"'},
        )
    return SuccessResponse(data=data)


@router.post(
    "",
    response_model=SuccessResponse[TicketDetail],
    status_code=status.HTTP_201_CREATED,
    summary="Create a support ticket",
)
async def create_ticket(
    body: TicketCreateRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    service = SuperAdminTicketListService(session)
    data = await service.create(body, current_user)
    return SuccessResponse(message="Ticket received. Assign it to Level 1.", data=data)


@router.patch(
    "",
    response_model=SuccessResponse[TicketDetail | BulkAssignResult | SlaSweepResult],
    summary="Assign, resolve, close, reopen, prioritize, add a note, or sweep SLA",
)
async def update_ticket(
    body: TicketActionRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
):
    service = SuperAdminTicketListService(session)
    data, message = await service.apply_action(body, current_user)
    return SuccessResponse(message=message, data=data)
