import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import DatabaseException
from ycpa.models.enquiry import ContactInformation
from ycpa.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContactRepository(BaseRepository[ContactInformation]):

    def __init__(self, session: AsyncSession):
        super().__init__(ContactInformation, session)

    async def get_by_ref(self, ref: str) -> ContactInformation | None:
        try:
            try:
                condition = ContactInformation.id == UUID(ref)
            except ValueError:
                condition = ContactInformation.contact_id == ref.strip().upper()

            result = await self.session.execute(
                select(ContactInformation).where(
                    condition,
                    ContactInformation.deleted_at.is_(None),
                )
            )
            return result.scalar_one_or_none()

        except DBAPIError as e:
            logger.error("DB error fetching contact", extra={"ref": ref, "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch contact enquiry")

    async def list_filtered(
        self,
        *,
        status: str | None = None,
        interested_in: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContactInformation], int]:
        try:
            conditions = [ContactInformation.deleted_at.is_(None)]

            if status:
                conditions.append(ContactInformation.status == status)
            if interested_in:
                conditions.append(ContactInformation.interested_in == interested_in)
            if search:
                term = f"%{search.strip()}%"
                conditions.append(or_(
                    ContactInformation.first_name.ilike(term),
                    ContactInformation.last_name.ilike(term),
                    ContactInformation.email.ilike(term),
                    ContactInformation.contact_id.ilike(term),
                ))

            total = (await self.session.execute(
                select(func.count()).select_from(ContactInformation).where(*conditions)
            )).scalar_one()

            rows = (await self.session.execute(
                select(ContactInformation)
                .where(*conditions)
                .order_by(ContactInformation.created_at.desc())
                .limit(limit)
                .offset(offset)
            )).scalars().all()

            return list(rows), total

        except DBAPIError as e:
            logger.error("DB error listing contacts", extra={"error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to fetch contact enquiries")

    async def mark_deleted(self, contact_id: UUID) -> None:
        try:
            await self.session.execute(
                update(ContactInformation)
                .where(ContactInformation.id == contact_id)
                .values(deleted_at=datetime.now(timezone.utc))
            )
            await self.session.flush()

        except DBAPIError as e:
            logger.error("DB error deleting contact", extra={"id": str(contact_id), "error": str(e)}, exc_info=True)
            raise DatabaseException("Failed to delete contact enquiry")