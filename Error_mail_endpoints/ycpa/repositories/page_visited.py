import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ycpa.models.page_visited import PageVisited
from ycpa.repositories.base import BaseRepository


class PageVisitedRepository(BaseRepository[PageVisited]):

    def __init__(self,session: AsyncSession):
        super().__init__(PageVisited,session)

    def _apply_date_filter(
            self,
            query,
            start_date : date | None,
            end_date : date | None,
    ):
        if start_date:
            query = query.where(
                func.date(PageVisited.created_at) >= start_date
            )
        if end_date :
            query = query.where(
                func.date(PageVisited.created_at) <= end_date
            )
        return query

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

    async def get_page_visits(
        self,
        *,
        country_name: str | None = None,
        page_name: str | None = None,
    ) -> list[PageVisited]:

        query = select(PageVisited)

        if country_name:
            query = query.where(
                func.lower(PageVisited.country_name) == country_name.lower()
            )

        if page_name:
            query = query.where(PageVisited.page_name == page_name)

        query = query.order_by(PageVisited.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_countries(
        self,
    ) -> list[str]:

        result = await self.session.execute(
            select(PageVisited.country_name)
            .where(PageVisited.country_name.is_not(None))
            .where(PageVisited.country_name != "")
            .distinct()
            .order_by(PageVisited.country_name)
        )

        return list(
            result.scalars().all()
        )

    async def get_pages(
        self,
    ) -> list[str]:

        result = await self.session.execute(
            select(PageVisited.page_name)
            .where(PageVisited.page_name.is_not(None))
            .where(PageVisited.page_name != "")
            .distinct()
            .order_by(PageVisited.page_name)
        )

        return list(
            result.scalars().all()
        )



    async def get_unique_visitors(
            self,
            start_date : date | None = None,
            end_date : date | None = None
    )-> int :
        query = select(
            func.count(
                func.distinct(PageVisited.ip_address)
            )
        ).where(
            PageVisited.ip_address.is_not(None)
        )
        query = self._apply_date_filter(
            query,
            start_date,
            end_date
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_total_page_views(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:

        query = select(
            func.count(PageVisited.id)
        )

        query = self._apply_date_filter(
            query,
            start_date,
            end_date,
        )

        result = await self.session.execute(query)

        return result.scalar() or 0

    async def get_average_visiting_time(
            self,
            start_date : date | None = None,
            end_date : date | None = None            
    ) -> float:
        query = select(
            func.avg(PageVisited.duration_seconds)
        ).where(
            PageVisited.duration_seconds.is_not(None)
        )
        query = self._apply_date_filter(
            query,
            start_date,
            end_date
        )
        result = await self.session.execute(query)
        value = result.scalar()
        return float(value or 0)

    async def get_acquisition_sources(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[tuple[str | None, object]]:

        query = select(
            PageVisited.previous_page,
            PageVisited.created_at,
        )

        query = self._apply_date_filter(
            query,
            start_date,
            end_date,
        )

        result = await self.session.execute(query)

        return list(result.all())

    async def get_session_by_device(self):
        query = select(
            PageVisited.device_type,
            func.count(PageVisited.id).label("sessions"),
        ).where(
            PageVisited.device_type.is_not(None)
            )
        query = query.group_by(
            PageVisited.device_type
        ).order_by(
            func.count(PageVisited.id).desc()
        )
        result = await self.session.execute(query)
        return result.all()