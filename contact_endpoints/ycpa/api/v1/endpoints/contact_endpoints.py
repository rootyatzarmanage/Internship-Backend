import logging
from typing import Optional

from fastapi import APIRouter, Query, status

from ycpa.core.auth.dependencies import SuperAdminUser
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.requests.contact import (ContactCreateRequest,ContactStatus,ContactStatusUpdateRequest)
from ycpa.schemas.responses.contact import (ContactListResponse,ContactResponse,ContactSubmitResponse)
from ycpa.services.contact import ContactService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact Us"])


@router.post(
    "",
    response_model=SuccessResponse[ContactSubmitResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit the Contact Us form (public)",
)
async def submit_contact_form(
    body: ContactCreateRequest,
    session: DatabaseSession,
) -> SuccessResponse[ContactSubmitResponse]:
    service = ContactService(session)
    result = await service.submit(body)
    return SuccessResponse(
        success=True,
        message="Thanks for reaching out. Our team will get back to you soon.",
        data=result,
    )

@router.get(
    "",
    response_model=SuccessResponse[ContactListResponse],
    status_code=status.HTTP_200_OK,
    summary="List contact enquiries (super admin)",
)
async def list_contacts(
    current_user: SuperAdminUser,
    session: DatabaseSession,
    status_filter: Optional[ContactStatus] = Query(None, alias="status"),
    interested_in: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Name, email or contact ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> SuccessResponse[ContactListResponse]:
    service = ContactService(session)
    result = await service.list_contacts(
        status=status_filter,
        interested_in=interested_in,
        search=search,
        page=page,
        per_page=per_page,
    )
    return SuccessResponse(success=True, data=result)


@router.get(
    "/{contact_ref}",
    response_model=SuccessResponse[ContactResponse],
    status_code=status.HTTP_200_OK,
    summary="Get one contact enquiry (super admin)",
)
async def get_contact(
    contact_ref: str,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[ContactResponse]:
    service = ContactService(session)
    result = await service.get_contact(contact_ref)
    return SuccessResponse(success=True, data=result)


@router.patch(
    "/{contact_ref}/status",
    response_model=SuccessResponse[ContactResponse],
    status_code=status.HTTP_200_OK,
    summary="Update enquiry status (super admin)",
)
async def update_contact_status(
    contact_ref: str,
    body: ContactStatusUpdateRequest,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[ContactResponse]:
    service = ContactService(session)
    result = await service.update_status(contact_ref, body.status, current_user.id)
    return SuccessResponse(success=True, message="Status updated.", data=result)


@router.delete(
    "/{contact_ref}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a contact enquiry (soft delete, super admin)",
)
async def delete_contact(
    contact_ref: str,
    current_user: SuperAdminUser,
    session: DatabaseSession,
) -> SuccessResponse[None]:
    service = ContactService(session)
    await service.delete_contact(contact_ref, current_user.id)
    return SuccessResponse(success=True, message="Enquiry deleted.")