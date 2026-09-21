import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from ycpa.models.page_visited import PageVisited
from ycpa.repositories.base import BaseRepository


class PageVisitedRepository(BaseRepository[PageVisited]):

    def __init__(self,session: AsyncSession):
        super().__init__(PageVisited,session)

    async def create_page_visit(
        self,
        *,
        page_name: str,
        page_url: str,
        previous_page: str | None,
        user_id: uuid.UUID | None,
        ip_address: str | None,
        country_name: str | None,
        region: str | None,
        city: str | None,
        pincode: str | None,
        device_type: str | None,
        operating_system: str | None,
        browser: str | None,
        time_zone: str | None,
        duration_seconds: int | None,
        created_by: uuid.UUID | None,
    ) -> PageVisited:
        page_visit = PageVisited(
            page_name=page_name,
            page_url=page_url,
            previous_page=previous_page,
            user_id=user_id,
            ip_address=ip_address,
            country_name=country_name,
            region=region,
            city=city,
            pincode=pincode,
            device_type=device_type,
            operating_system=operating_system,
            browser=browser,
            time_zone=time_zone,
            duration_seconds=duration_seconds,
            created_by=created_by,
        )
        self.session.add(page_visit)
        await self.session.flush()
        return page_visit
