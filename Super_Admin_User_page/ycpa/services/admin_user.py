import calendar
from datetime import datetime, timezone

from ycpa.repositories.admin_user import AdminUserRepository


class AdminUserService:

    def __init__(
        self,
        repository: AdminUserRepository,
    ):
        self.repository = repository

    @staticmethod
    def _current_month_range():

        now = datetime.now(timezone.utc)
        start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

        if now.month == 12:
            end = datetime(
                now.year + 1,
                1,
                1,
                tzinfo=timezone.utc,
            )

        else:
            end = datetime(
                now.year,
                now.month + 1,
                1,
                tzinfo=timezone.utc,
            )
        return start, end

    @staticmethod
    def _previous_month_range():
        now = datetime.now(timezone.utc)
        current_start = datetime(
            now.year,
            now.month,
            1,
            tzinfo=timezone.utc,
        )

        if now.month == 1:
            previous_start = datetime(
                now.year - 1,
                12,
                1,
                tzinfo=timezone.utc,
            )

        else:

            previous_start = datetime(
                now.year,
                now.month - 1,
                1,
                tzinfo=timezone.utc,
            )
        return previous_start, current_start

    @staticmethod
    def _percentage_change(
        current: int,
        previous: int,
    ) -> float:

        if previous == 0:

            if current == 0:
                return 0.0

            return 100.0

        return round(
            (
                (current - previous)
                / previous
            )
            * 100,
            2,
        )

    async def get_total_users(self):

        total = (
            await self.repository
            .get_total_users()
        )

        current_start, current_end = (
            self._current_month_range()
        )

        previous_start, previous_end = (
            self._previous_month_range()
        )

        current = (
            await self.repository
            .get_users_between(
                current_start,
                current_end,
            )
        )

        previous = (
            await self.repository
            .get_users_between(
                previous_start,
                previous_end,
            )
        )

        return {
            "value": total,
            "percentage_change": (
                self._percentage_change(
                    current,
                    previous,
                )
            ),
        }

    async def get_active_users(self):

        total = (
            await self.repository
            .get_active_users()
        )

        current_start, current_end = (
            self._current_month_range()
        )

        previous_start, previous_end = (
            self._previous_month_range()
        )

        current = (
            await self.repository
            .get_active_users_between(
                current_start,
                current_end,
            )
        )

        previous = (
            await self.repository
            .get_active_users_between(
                previous_start,
                previous_end,
            )
        )

        return {
            "value": total,
            "percentage_change": (
                self._percentage_change(
                    current,
                    previous,
                )
            ),
        }

    async def get_verified_users(self):

        total = (
            await self.repository
            .get_verified_users()
        )

        current_start, current_end = (
            self._current_month_range()
        )

        previous_start, previous_end = (
            self._previous_month_range()
        )

        current = (
            await self.repository
            .get_verified_users_between(
                current_start,
                current_end,
            )
        )

        previous = (
            await self.repository
            .get_verified_users_between(
                previous_start,
                previous_end,
            )
        )

        return {
            "value": total,
            "percentage_change": (
                self._percentage_change(
                    current,
                    previous,
                )
            ),
        }
    
    async def get_new_signups(self):

        current_start, current_end = (
            self._current_month_range()
        )

        previous_start, previous_end = (
            self._previous_month_range()
        )

        current = (
            await self.repository
            .get_new_signups(
                current_start,
                current_end,
            )
        )

        previous = (
            await self.repository
            .get_new_signups(
                previous_start,
                previous_end,
            )
        )

        return {
            "value": current,
            "percentage_change": (
                self._percentage_change(
                    current,
                    previous,
                )
            ),
        }

    async def get_users(
        self,
        search: str | None = None,
        page: int = 1,
        limit: int = 6,
    ):

        if page < 1:
            page = 1

        if limit < 1:
            limit = 6

        offset = (
            (page - 1)
            * limit
        )

        rows = (
            await self.repository
            .get_users(
                search=search,
                limit=limit,
                offset=offset,
            )
        )

        total = (
            await self.repository
            .count_users(
                search=search
            )
        )

        items = []

        for row in rows:

            items.append(
                {
                    "user_id": str(row.id),
                    "name": row.full_name,
                    "email": row.email,
                    "phone_number": row.phone,
                    "workspace_count": int(
                        row.workspace_count
                        or 0
                    ),
                    "projects": int(
                        row.project_count
                        or 0
                    ),
                    "status": row.status,
                    "verified": bool(row.email_verified),
                    "last_login": row.last_login_at,
                    "registered": row.created_at,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
        }
    
    async def get_verified_status(
        self,
        year: int,
    ):

        rows = (
            await self.repository
            .get_verified_status_by_year(
                year
            )
        )

        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        result = []

        row_map = {
            int(row.month): row
            for row in rows
        }

        for month in range(1, 13):

            row = row_map.get(month)
            result.append(
                {
                    "month": month_names[
                        month - 1
                    ],

                    "verified": (
                        int(row.verified or 0)
                        if row
                        else 0
                    ),

                    "not_verified": (
                        int(
                            row.not_verified
                            or 0
                        )
                        if row
                        else 0
                    ),
                }
            )

        return {
            "year": year,
            "items": result,
        }

    async def get_users_by_status(self):

        rows = (
            await self.repository
            .get_users_by_status()
        )
        status_order = {
            "Deactive": 0,
            "Offline": 1,
            "Active": 2,
        }

        result = [
            {
                "status": status,
                "count": int(count),
            }
            for status, count in rows
        ]

        result.sort(
            key=lambda item: status_order.get(
                item["status"],
                99,
            )
        )

        return result