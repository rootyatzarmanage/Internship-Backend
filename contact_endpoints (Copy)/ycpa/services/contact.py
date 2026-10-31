import logging
from math import ceil
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import NotFoundException
from ycpa.models.enquiry import ContactInformation
from ycpa.repositories.contact import ContactRepository
from ycpa.schemas.requests.contact import ContactCreateRequest
from ycpa.schemas.responses.contact import (
    ContactListResponse,
    ContactResponse,
    ContactSubmitResponse,
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class ContactService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.contact_repo = ContactRepository(session)

    async def submit(self, data: ContactCreateRequest) -> ContactSubmitResponse:
        contact = await self.contact_repo.create(
            ContactInformation(
                first_name=data.first_name,
                last_name=data.last_name,
                email=str(data.email).lower(),
                phone_country_code=data.phone_country_code,
                phone=data.phone,
                interested_in=data.interested_in,
                message=data.message,
                status="new",
            )
        )  
        await self.session.commit()

        logger.info(
            "Contact enquiry submitted",
            extra={"contact_id": contact.contact_id, "email": contact.email},
        )
        return ContactSubmitResponse.model_validate(contact)

    async def list_contacts(
        self,
        *,
        status: str | None,
        interested_in: str | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> ContactListResponse:
        rows, total = await self.contact_repo.list_filtered(
            status=status,
            interested_in=interested_in,
            search=search,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return ContactListResponse(
            items=[ContactResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_contact(self, ref: str) -> ContactResponse:
        contact = await self._get_or_404(ref)
        return ContactResponse.model_validate(contact)

    async def update_status(self, ref: str, new_status: str, admin_id: UUID) -> ContactResponse:
        contact = await self._get_or_404(ref)
        old_status = contact.status

        contact = await self.contact_repo.update_by_id(contact.id, {"status": new_status})

        await self.log_audit(
            action="CONTACT_STATUS_UPDATED",
            resource_type="contact_information",
            resource_id=contact.contact_id,
            user_id=admin_id,
            changed_from={"status": old_status},
            changed_to={"status": new_status},
        )
        await self.session.commit()
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, ref: str, admin_id: UUID) -> None:
        contact = await self._get_or_404(ref)
        await self.contact_repo.mark_deleted(contact.id)

        await self.log_audit(
            action="CONTACT_DELETED",
            resource_type="contact_information",
            resource_id=contact.contact_id,
            user_id=admin_id,
        )
        await self.session.commit()

    async def _get_or_404(self, ref: str) -> ContactInformation:
        contact = await self.contact_repo.get_by_ref(ref)
        if not contact:
            raise NotFoundException("Contact enquiry not found", resource="contact_information")
        return contact