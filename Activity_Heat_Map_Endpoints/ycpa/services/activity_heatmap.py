import logging
from calendar import monthrange
from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.activity_heat_map import ActivityHeatMapRepository
from ycpa.schemas.responses.activity_heat_map import ActivityHeatMapResponse


logger = logging.getLogger(__name__)


HeatMapFilter = Literal[
    "all",
    "projects",
    "meetings",
    "workspaces",
]


WEEKDAYS = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
]


class ActivityHeatmapService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.repository = (
            ActivityHeatMapRepository(session)
        )

    @staticmethod
    def _safe_timezone(
        value: str | None,
    ) -> ZoneInfo:
        try:
            return ZoneInfo(
                value or "UTC"
            )
        except Exception:
            return ZoneInfo("UTC")

    @staticmethod
    def _six_completed_months(
        today: date,
    ):
        first_current_month = (
            today.replace(day=1)
        )
        end_date = (
            first_current_month
            - timedelta(days=1)
        )
        months = []
        cursor = end_date.replace(day=1)
        for _ in range(6):
            month_end = cursor.replace(
                day=monthrange(
                    cursor.year,
                    cursor.month,
                )[1]
            )
            months.append(
                {
                    "key": cursor.strftime("%Y-%m"),
                    "label": cursor.strftime("%b"),
                    "year": cursor.year,
                    "month": cursor.month,
                    "start_date": (cursor.isoformat()),
                    "end_date": (month_end.isoformat()),
                }
            )

            cursor = (
                cursor
                - timedelta(days=1)
            ).replace(day=1)

        months.reverse()

        return (
            date.fromisoformat(
                months[0]["start_date"]
            ),

            date.fromisoformat(
                months[-1]["end_date"]
            ),

            months,
        )

    @staticmethod
    def _utc_range(
        start_date: date,
        end_date: date,
        timezone_info: ZoneInfo,
    ):
        start_local = datetime.combine(
            start_date,
            time.min,
            tzinfo=timezone_info,
        )

        end_local = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=timezone_info,
        )

        return (
            start_local.astimezone(timezone.utc),
            end_local.astimezone(timezone.utc),
        )

    @staticmethod
    def _build_days(
        start_date: date,
        end_date: date,
        counts: dict[date, int],
    ):
        days = []
        cursor = start_date
        while cursor <= end_date:
            value = int(
                counts.get(
                    cursor,
                    0,
                )
            )
            if value == 0:
                intensity = "none"

            elif value <= 25:
                intensity = "low"

            elif value <= 75:
                intensity = "medium"

            else:
                intensity = "high"

            days.append(
                {
                    "date": cursor,

                    "day": cursor.day,

                    "weekday": cursor.strftime(
                        "%a"
                    ),

                    "weekday_index": (
                        cursor.weekday()
                    ),

                    "month": cursor.strftime(
                        "%b"
                    ),

                    "month_key": cursor.strftime(
                        "%Y-%m"
                    ),

                    "value": value,

                    "intensity": intensity,
                }
            )

            cursor += timedelta(
                days=1
            )

        return days

    @staticmethod
    def _calculate_longest_streak(
        days,
    ):
        longest = 0
        longest_start = None
        longest_end = None
        current = 0
        current_start = None
        for item in days:
            current_date = item["date"]
            if item["value"] > 0:
                if current == 0:
                    current_start = (
                        current_date
                    )

                current += 1

                if current > longest:

                    longest = current

                    longest_start = (
                        current_start
                    )

                    longest_end = (
                        current_date
                    )

            else:
                current = 0
                current_start = None

        return (
            longest,
            longest_start,
            longest_end,
        )

    @staticmethod
    def _build_calendar_series(
        start_date: date,
        end_date: date,
        days,
    ):
        day_map = {
            item["date"]: item
            for item in days
        }
        first_monday = (
            start_date
            - timedelta(
                days=start_date.weekday()
            )
        )
        last_sunday = (
            end_date
            + timedelta(
                days=6 - end_date.weekday()
            )
        )
        weeks = []
        cursor = first_monday
        while cursor <= last_sunday:
            weeks.append(cursor)
            cursor += timedelta(
                days=7
            )
        series = []
        for weekday_index, weekday in enumerate(
            WEEKDAYS
        ):
            data = []
            for week_start in weeks:
                cell_date = (
                    week_start
                    + timedelta(
                        days=weekday_index
                    )
                )
                in_period = (
                    start_date
                    <= cell_date
                    <= end_date
                )
                item = (
                    day_map.get(cell_date)
                    if in_period
                    else None
                )
                data.append(
                    {
                        "x": (
                            week_start.isoformat()
                        ),

                        "y": (
                            item["value"]
                            if item
                            else None
                        ),

                        "date": cell_date,

                        "weekday": weekday,

                        "weekday_index": (
                            weekday_index
                        ),

                        "month": (
                            cell_date.strftime(
                                "%b"
                            )
                        ),

                        "month_key": (
                            cell_date.strftime(
                                "%Y-%m"
                            )
                        ),

                        "in_period": in_period,

                        "intensity": (
                            item["intensity"]
                            if item
                            else None
                        ),
                    }
                )

            series.append(
                {
                    "name": weekday,
                    "data": data,
                }
            )

        week_meta = [
            {
                "key": week.isoformat(),

                "label": week.strftime(
                    "%d %b"
                ),

                "start_date": week,

                "end_date": (
                    week
                    + timedelta(days=6)
                ),
            }
            for week in weeks
        ]

        return (
            series,
            week_meta,
        )

    async def get_activity_heat_map(
        self,
        current_user,
        category: HeatMapFilter = "all",
    ) -> ActivityHeatMapResponse:

        timezone_info = (
            self._safe_timezone(
                getattr(
                    current_user,
                    "timezone",
                    None,
                )
            )
        )
        today = datetime.now(
            timezone_info
        ).date()

        (
            start_date,
            end_date,
            months,
        ) = self._six_completed_months(
            today
        )

        (
            start_utc,
            end_utc,
        ) = self._utc_range(
            start_date,
            end_date,
            timezone_info,
        )
        daily_counts = (
            await self.repository
            .get_daily_activity_counts(
                user_id=current_user.id,

                start_utc=start_utc,

                end_utc=end_utc,

                timezone_name=str(
                    timezone_info
                ),
                category=category,
            )
        )

        days = self._build_days(
            start_date,
            end_date,
            daily_counts,
        )

        (
            series,
            weeks,
        ) = self._build_calendar_series(
            start_date,
            end_date,
            days,
        )

        total_activities = sum(
            item["value"]
            for item in days
        )

        weekday_totals = {
            weekday: 0
            for weekday in WEEKDAYS
        }

        for item in days:

            weekday_totals[
                item["weekday"]
            ] += item["value"]

        busiest_day = max(
            WEEKDAYS,
            key=lambda weekday: (
                weekday_totals[weekday],
                -WEEKDAYS.index(weekday),
            ),
        )

        busiest_date = max(
            days,
            key=lambda item: (
                item["value"],
                item["date"],
            ),
            default=None,
        )

        (
            longest_streak,
            streak_start,
            streak_end,
        ) = self._calculate_longest_streak(
            days
        )

        return ActivityHeatMapResponse(

            filter=category,

            period={
                "months": 6,

                "type": (
                    "last_6_completed_months"
                ),

                "timezone": str(
                    timezone_info
                ),

                "start_date": start_date,

                "end_date": end_date,
            },

            summary={
                "total_activities": (
                    total_activities
                ),

                "busiest_day": (
                    busiest_day
                ),

                "busiest_day_activity_count":
                    weekday_totals[
                        busiest_day
                    ],

                "busiest_date": (
                    busiest_date["date"]
                    if busiest_date
                    else None
                ),

                "busiest_date_activity_count":
                    (
                        busiest_date["value"]
                        if busiest_date
                        else 0
                    ),

                "longest_streak": (
                    longest_streak
                ),

                "longest_streak_start": (
                    streak_start
                ),

                "longest_streak_end": (
                    streak_end
                ),
            },

            filters={
                "selected": category,

                "available": [
                    "all",
                    "projects",
                    "meetings",
                    "workspaces",
                ],
            },

            months=months,

            weeks=weeks,

            weekdays=WEEKDAYS,

            weekday_totals=weekday_totals,

            days=days,

            series=series,

            legend={
                "min_label": "Less",

                "max_label": "More",

                "levels": [
                    "none",
                    "low",
                    "medium",
                    "high",
                ],
            },
        )