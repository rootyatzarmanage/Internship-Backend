import uuid
from datetime import date,timedelta
from urllib.parse import urlparse
from typing import Any
from dateutil.relativedelta import relativedelta

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

    def _get_previous_month_range(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[date, date]:

        previous_start = start_date - relativedelta(months=1)
        previous_end = end_date - relativedelta(months=1)

        return previous_start, previous_end

    def _calculate_percentage_change(
        self,
        current_value: float,
        previous_value: float,
    ) -> float:

        if previous_value == 0:
            if current_value == 0:
                return 0.0

            return 100.0

        return round(
            ((current_value - previous_value) / previous_value) * 100,
            2,
        )
    def _get_current_month_range(self):
        today = date.today()

        current_start = today.replace(day=1)

        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1,
                month=1,
                day=1,
            )
        else:
            next_month = today.replace(
                month=today.month + 1,
                day=1,
            )

        current_end = next_month - timedelta(days=1)

        return current_start, current_end

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
        *,
        country_name: str | None = None,
        page_name: str | None = None,
    ) -> list[PageVisited] :

        return await self.repository.get_page_visits(
            country_name=country_name,
            page_name=page_name,
        )

    async def get_countries(
        self,
    ) -> list[str]:

        return await self.repository.get_countries()


    async def get_pages(
        self,
    ) -> list[str]:

        return await self.repository.get_pages()

    async def get_unique_visitors(self) -> dict:
        total_value = await self.repository.get_unique_visitors()
        current_start, current_end = self._get_current_month_range()
        current_month_value = await self.repository.get_unique_visitors(
            start_date=current_start,
            end_date=current_end,
        )
        previous_start, previous_end = self._get_previous_month_range(
            start_date=current_start,
            end_date=current_end,
        )
        previous_month_value = await self.repository.get_unique_visitors(
            start_date=previous_start,
            end_date=previous_end,
        )
        percentage_change = self._calculate_percentage_change(
            current_value=current_month_value,
            previous_value=previous_month_value,
        )
        return {
            "value": total_value,
            "percentage_change": percentage_change,
        }

    async def get_total_page_views(self) -> dict:
        total_value = await self.repository.get_total_page_views()
        current_start, current_end = self._get_current_month_range()
        current_month_value = await self.repository.get_total_page_views(
            start_date=current_start,
            end_date=current_end,
        )
        previous_start, previous_end = self._get_previous_month_range(
            start_date=current_start,
            end_date=current_end,
        )
        previous_month_value = await self.repository.get_total_page_views(
            start_date=previous_start,
            end_date=previous_end,
        )
        percentage_change = self._calculate_percentage_change(
            current_value=current_month_value,
            previous_value=previous_month_value,
        )
        return {
            "value": total_value,
            "percentage_change": percentage_change,
        }

    async def get_average_visiting_time(self) -> dict:
        total_average = await self.repository.get_average_visiting_time()
        current_start, current_end = self._get_current_month_range()
        current_month_average = await self.repository.get_average_visiting_time(
            start_date=current_start,
            end_date=current_end,
        )
        previous_start, previous_end = self._get_previous_month_range(
            start_date=current_start,
            end_date=current_end,
        )
        previous_month_average = await self.repository.get_average_visiting_time(
            start_date=previous_start,
            end_date=previous_end,
        )
        percentage_change = self._calculate_percentage_change(
            current_value=current_month_average,
            previous_value=previous_month_average,
        )
        return {
            "value": round(total_average / 60, 2),
            "percentage_change": percentage_change,
        }


    async def get_acquisition_channel(
        self,
    ) -> list[dict]:
        today = date.today()
        current_month_start = today.replace(day=1)
        month = current_month_start.month
        year = current_month_start.year
        months_to_go_back = 5
        month = month - months_to_go_back
        while month <= 0:
            month += 12
            year -= 1

        six_month_start = date(
            year,
            month,
            1,
        )
        if current_month_start.month == 12:
            next_month_start = date(
                current_month_start.year + 1,
                1,
                1,
            )
        else:
            next_month_start = date(
                current_month_start.year,
                current_month_start.month + 1,
                1,
            )
        six_month_end = next_month_start - timedelta(days=1)
        rows = await self.repository.get_acquisition_sources(
            start_date=six_month_start,
            end_date=six_month_end,
        )
        monthly_channels = {}
        current_month = six_month_start
        for _ in range(6):
            month_key = (
                current_month.year,
                current_month.month,
            )
            monthly_channels[month_key] = {
                "Direct": 0,
                "Referral": 0,
                "Social": 0,
                "SEO": 0,
            }
            if current_month.month == 12:
                current_month = date(
                    current_month.year + 1,
                    1,
                    1,
                )
            else:
                current_month = date(
                    current_month.year,
                    current_month.month + 1,
                    1,
                )
        for previous_page, created_at in rows:
            if created_at is None:
                continue

            visit_date = created_at.date()
            month_key = (
                visit_date.year,
                visit_date.month,
            )
            if month_key not in monthly_channels:
                continue
            channel = self._classify_acquisition(
                previous_page
            )
            monthly_channels[month_key][channel] += 1
        response = []

        for (
            year,
            month_number,
        ), channels in monthly_channels.items():

            month_name = date(
                year,
                month_number,
                1,
            ).strftime("%b")
            response.append(
                {
                    "month": month_name,
                    "channels": [
                        {
                            "channel": "Direct",
                            "count": channels["Direct"],
                        },
                        {
                            "channel": "Referral",
                            "count": channels["Referral"],
                        },
                        {
                            "channel": "Social",
                            "count": channels["Social"],
                        },
                        {
                            "channel": "SEO",
                            "count": channels["SEO"],
                        },
                    ],
                }
            )

        return response
    @staticmethod
    def _classify_acquisition(
        previous_page: str | None
    ) -> str:

        if not previous_page:
            return "Direct"

        value = previous_page.strip().lower()
        if value.startswith("/"):
            return "Direct"

        referral_sources = [
            "chatgpt.com",
            "://openai.com",
            "openai.com",
            "perplexity.ai",
            "www.perplexity.ai",
            "claude.ai",
            "://microsoft.com",
            "meta.ai",
            "you.com",
            "phind.com",
            "deepseek.com",
            "mistral.ai",
        ]

        if any(
            source in value
            for source in referral_sources
        ):
            return "Referral"

        social_sources = [
            "linkedin.com",
            "lnkd.in",
            "instagram.com",
            "l.instagram.com",
            "facebook.com",
            "l.facebook.com",
            "m.facebook.com",
            "twitter.com",
            "t.co",
            "x.com",
            "youtube.com",
            "youtu.be",
            "tiktok.com",
            "vm.tiktok.com",
            "reddit.com",
            "://reddit.com",
            "quora.com",
            "pinterest.com",
            "tumblr.com",
            "threads.net",
            "bluesky.social",
            "bsky.app",
            "mastodon.social",
            "t.me",
            "whatsapp.com",
            "://whatsapp.com",
            "discord.com",
            "discordapp.com",
        ]

        if any(
            source in value
            for source in social_sources
        ):
            return "Social"

        search_sources = [
            "google.com",
            "google.co.in",
            "google.co.uk",
            "google.ca",
            "google.de",
            "bing.com",
            "yahoo.com",
            "search.yahoo.com",
            "duckduckgo.com",
            "ddg.gg",
            "brave.com",
            "search.brave.com",
            "yandex.com",
            "yandex.ru",
            "baidu.com",
            "ecosia.org",
            "startpage.com",
            "qwant.com",
            "mojeek.com",
            "searx.space",
            "naver.com",
            "daum.net",
            "seznam.cz",
            "rambler.ru",
            "mail.ru",
            "so.com",
            "sogou.com",
            "aol.com",
            "://aol.com",
            "ask.com",
        ]

        if any(
            source in value
            for source in search_sources
        ):
            return "SEO"

        return "Referral"

    async def get_session_by_device(
        self,
    ):
        rows = await self.repository.get_session_by_device()

        device_counts = {
            "Mobile": 0,
            "Tablet": 0,
            "Laptop / PC": 0,
        }

        for device, sessions in rows:

            if device is None:
                continue

            if device.lower() == "mobile":
                device_counts["Mobile"] += sessions

            elif device.lower() == "tablet":
                device_counts["Tablet"] += sessions

            elif device.lower() in ["desktop", "laptop", "laptop / pc"]:
                device_counts["Laptop / PC"] += sessions

        return [
            {
                "device": "Mobile",
                "sessions": device_counts["Mobile"],
            },
            {
                "device": "Tablet",
                "sessions": device_counts["Tablet"],
            },
            {
                "device": "Laptop / PC",
                "sessions": device_counts["Laptop / PC"],
            },
        ]

            