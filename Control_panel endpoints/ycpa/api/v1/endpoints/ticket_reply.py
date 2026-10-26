from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from ycpa.core.auth.dependencies import CurrentUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.ticket_reply import CreateReplyRequest, UpdateTicketStatusRequest, create_reply_form
from ycpa.schemas.responses.ticket_reply import MessageResponse, TicketDetailsResponse, TicketThreadResponse
from ycpa.services.ticket_reply import TicketReplyService

router = APIRouter(prefix="/ticket-reply", tags=["Ticket Reply"])


@router.get("/{ticket_id}", response_model=SuccessResponse[TicketThreadResponse], summary="Ticket thread + details + prev/next")
async def get_thread(ticket_id: UUID, session: DatabaseSession, current_user: CurrentUser):
    return SuccessResponse(data=await TicketReplyService(session).get_thread(current_user, ticket_id))


@router.post("/{ticket_id}/replies", response_model=SuccessResponse[MessageResponse], status_code=status.HTTP_201_CREATED, summary="Reply to a ticket")
async def add_reply(
    ticket_id: UUID, session: DatabaseSession, current_user: CurrentUser,
    data: Annotated[CreateReplyRequest, Depends(create_reply_form)],
    files: Annotated[
        list[UploadFile],
        File(
            description="Optional attachments: PDF, JPG, PNG, DOCX; maximum 5 files, 10 MB per file",
            json_schema_extra={"items": {"type": "string", "format": "binary"}},
        ),
    ] = [],
):
    return SuccessResponse(message="Reply sent.", data=await TicketReplyService(session).add_reply(current_user, ticket_id, data, files))


@router.patch("/{ticket_id}/status", response_model=SuccessResponse[TicketDetailsResponse], summary="Set status: pending | in_progress | solved | on_hold")
async def update_status(ticket_id: UUID, body: UpdateTicketStatusRequest, session: DatabaseSession, current_user: CurrentUser):
    return SuccessResponse(message="Status updated.", data=await TicketReplyService(session).update_status(current_user, ticket_id, body))
