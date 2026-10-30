import logging
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import ConflictException, NotFoundException
from ycpa.models.faq import Faq
from ycpa.models.user import User
from ycpa.repositories.faq import FaqRepository
from ycpa.schemas.requests.faq import FaqCreateRequest, FaqUpdateRequest
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class FaqService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = FaqRepository(session)

    async def _get_or_404(self, faq_id: UUID) -> Faq:
        faq = await self.repo.get_by_id(faq_id)
        if not faq:
            raise NotFoundException("FAQ not found", resource="faq")
        return faq

    async def list_public(self) -> list[Faq]:
        return await self.repo.list_faqs(is_active=1, limit=500)

    async def get_public(self, faq_id: UUID) -> Faq:
        faq = await self._get_or_404(faq_id)
        if not faq.is_active:
            raise NotFoundException("FAQ not found", resource="faq")
        return faq

    async def list_manage(
        self,
        search: str | None,
        is_active: bool | None,
        page: int,
        per_page: int,
    ) -> tuple[list[Faq], int]:
        active = None if is_active is None else int(is_active)
        total = await self.repo.count_faqs(is_active=active, search=search)
        items = await self.repo.list_faqs(
            is_active=active,
            search=search,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return items, total

    async def get_faq(self, faq_id: UUID) -> Faq:
        return await self._get_or_404(faq_id)

    async def create_faq(self, user: User, data: FaqCreateRequest) -> Faq:
        if await self.repo.get_by_question(data.question):
            raise ConflictException("An FAQ with this question already exists")

        display_order = data.display_order
        if display_order is None:
            display_order = await self.repo.get_next_display_order()

        faq = await self.repo.create(Faq(
            question=data.question,
            answer=data.answer,
            display_order=display_order,
            is_active=int(data.is_active),
            created_by=user.id,
            updated_by=user.id,
        ))

        await self.log_audit(
            action="faq.create",
            resource_type="faq",
            resource_id=str(faq.id),
            user_id=user.id,
            changed_to={"question": faq.question, "display_order": faq.display_order, "is_active": faq.is_active},
        )
        await self.session.commit()
        logger.info("FAQ created", extra={"faq_id": str(faq.id), "user_id": str(user.id)})
        return faq

    async def update_faq(self, user: User, faq_id: UUID, data: FaqUpdateRequest) -> Faq:
        faq = await self._get_or_404(faq_id)

        if await self.repo.get_by_question(data.question, exclude_id=faq.id):
            raise ConflictException("An FAQ with this question already exists")

        changed_from = {
            "question": faq.question,
            "answer": faq.answer,
            "display_order": faq.display_order,
            "is_active": faq.is_active,
        }

        values: dict = {
            "question": data.question,
            "answer": data.answer,
            "updated_by": user.id,
        }
        if data.display_order is not None:
            values["display_order"] = data.display_order
        if data.is_active is not None:
            values["is_active"] = int(data.is_active)

        updated = await self.repo.update_by_id(faq.id, values)

        await self.log_audit(
            action="faq.update",
            resource_type="faq",
            resource_id=str(faq_id),
            user_id=user.id,
            changed_from=changed_from,
            changed_to=jsonable_encoder(
                {k: v for k, v in values.items() if k != "updated_by"}
            ),
        )
        await self.session.commit()
        logger.info("FAQ updated", extra={"faq_id": str(faq_id), "user_id": str(user.id)})
        return updated

    async def delete_faq(self, user: User, faq_id: UUID) -> None:
        faq = await self._get_or_404(faq_id)

        await self.repo.soft_delete(faq.id, deleted_by=user.id)

        await self.log_audit(
            action="faq.delete",
            resource_type="faq",
            resource_id=str(faq_id),
            user_id=user.id,
            changed_from={"question": faq.question},
        )
        await self.session.commit()
        logger.info("FAQ deleted", extra={"faq_id": str(faq_id), "user_id": str(user.id)})
