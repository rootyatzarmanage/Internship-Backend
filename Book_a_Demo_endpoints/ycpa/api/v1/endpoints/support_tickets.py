from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.support_tickets import CreateTicketRequest, create_ticket_form
from ycpa.schemas.responses.support_tickets import MyTicketsResponse, ProjectCardResponse, TicketResponse
from ycpa.services.support_tickets import SupportTicketService

router = APIRouter(prefix="/support-tickets", tags=["Support Tickets"])


@router.get("/projects", response_model=SuccessResponse[list[ProjectCardResponse]], summary="Project cards for 'Add product'")
async def list_projects(
    session: DatabaseSession, current_user: CurrentUser,
    q: str | None = Query(None, description="Search by project name"),
    limit: int = Query(50, le=100),
):
    return SuccessResponse(data=await SupportTicketService(session).list_projects(current_user, q, limit))



@router.post(
    "",
    response_model=SuccessResponse[TicketResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a support ticket",
)
async def create_ticket(
    session: DatabaseSession,
    current_user: CurrentUser,
    data: Annotated[
        CreateTicketRequest,
        Depends(create_ticket_form),
    ],
    files: Annotated[
        list[UploadFile],
        File(
            description="Optional attachments: PDF, JPG, PNG, DOCX; maximum 5 files, 10 MB per file",
            json_schema_extra={"items": {"type": "string", "format": "binary"}},
        ),
    ] = [],
):
    ticket = await SupportTicketService(session).create_ticket(
        current_user,
        data,
        files,
    )
    return SuccessResponse(
        message="Ticket submitted.",
        data=ticket,
    )



@router.get("/my", response_model=SuccessResponse[MyTicketsResponse], summary="My tickets")
async def my_tickets(
    session: DatabaseSession, current_user: CurrentUser,
    page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100),
):
    return SuccessResponse(data=await SupportTicketService(session).my_tickets(current_user, page, per_page))
