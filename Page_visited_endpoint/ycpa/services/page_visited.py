import uuid

import ipaddress
from fastapi import Request
from ycpa.core.request import get_client_ip
from ycpa.repositories.page_visited import PageVisitedRepository
from ycpa.services.analytics.ip_location import IPLocationService
from ycpa.services.analytics.user_agent_parser import UserAgentParser
from ycpa.schemas.requests.page_visited import PageVisitedRequest
from ycpa.models.page_visited import PageVisited


class PageVisitedService:

    def __init__(
        self,
        repository: PageVisitedRepository,
    ):
        self.repository = repository
        self.ip_location_service = IPLocationService()
        self.user_agent_parser = UserAgentParser()

    async def create_page_visit(
        self,
        *,
        request: Request,
        payload: PageVisitedRequest,
        user_id: uuid.UUID | None,
    ):

        ip_address = get_client_ip(request)
        location_data: dict = {}
        if ip_address:
            try: 
                ip = ipaddress.ip_address(ip_address)
                if ip.is_global:
                    location_data = (
                        await self.ip_location_service.get_location(
                            ip_address
                        )
                    ) or {}
                else:
                    location_data = (
                        await self.ip_location_service
                        .get_my_public_location()
                    ) or {}

                    ip_address = location_data.get(
                        "ip_address"
                    )
            except ValueError:
                location_data = {}

        user_agent = request.headers.get(
            "user-agent"
        )
        operating_system = None
        browser = None
        device_type = None

        if user_agent:
            operating_system = (
                self.user_agent_parser
                .get_operating_system(
                    user_agent
                )
            )
            browser = (
                self.user_agent_parser
                .get_browser(
                    user_agent
                )
            )
            device_type = (
                self.user_agent_parser
                .get_device_type(
                    user_agent
                )
            )
        page_visit = (
            await self.repository.create_page_visit(
                page_name=payload.page_name,
                page_url=payload.page_url,
                previous_page=payload.previous_page,
                user_id=user_id,
                ip_address=ip_address,
                country_name=location_data.get("country_name"),
                region=location_data.get("region"),
                city=location_data.get("city"),
                pincode=location_data.get("pincode"),
                device_type=device_type,
                operating_system=operating_system,
                browser=browser,
                time_zone=location_data.get("time_zone"),
                duration_seconds=payload.duration_seconds,
                created_by=user_id,
            )
        )

        return page_visit

    async def get_page_visits(
        self,
    ) -> list[PageVisited]:
        return await self.repository.get_page_visits()

    async def get_page_visits_by_country(
        self,
        country_name: str,
    ) -> list[PageVisited]:
        return await self.repository.get_page_visits_by_country(
            country_name
        )

    async def get_page_visits_by_page(
        self,
        page_name: str,
    ) -> list[PageVisited]:
        return await self.repository.get_page_visits_by_page(
            page_name
        )