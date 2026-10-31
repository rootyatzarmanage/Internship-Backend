import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.superadmin_pricing import SuperadminPricing
from ycpa.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

PRICING_SLUG = "pricing"


class SuperadminPricingRepository(BaseRepository[SuperadminPricing]):

    def __init__(self, session: AsyncSession):
        super().__init__(SuperadminPricing, session)

    async def get_pricing(self) -> SuperadminPricing | None:
        return await self.get_by_field("slug", PRICING_SLUG)
