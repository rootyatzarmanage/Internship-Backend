from datetime import date
from typing import Literal

from pydantic import BaseModel


class HeatMapPeriodResponse(BaseModel):
    months: int
    type: str
    timezone: str
    start_date: date
    end_date: date


class HeatMapSummaryResponse(BaseModel):
    total_activities: int
    busiest_day: str
    busiest_day_activity_count: int
    busiest_date: date | None = None
    busiest_date_activity_count: int = 0
    longest_streak: int
    longest_streak_start: date | None = None
    longest_streak_end: date | None = None


class HeatMapFiltersResponse(BaseModel):
    selected: Literal[
        "all",
        "projects",
        "meetings",
        "workspaces",
    ]

    available: list[str]


class HeatMapMonthResponse(BaseModel):
    key: str
    label: str
    year: int
    month: int
    start_date: date
    end_date: date


class HeatMapWeekResponse(BaseModel):
    key: str
    label: str
    start_date: date
    end_date: date


class HeatMapDayResponse(BaseModel):
    date: date
    day: int
    weekday: str
    weekday_index: int
    month: str
    month_key: str
    value: int
    intensity: Literal[
        "none",
        "low",
        "medium",
        "high",
    ]


class HeatMapCellResponse(BaseModel):
    x: str
    y: int | None
    date: date
    weekday: str
    weekday_index: int
    month: str
    month_key: str
    in_period: bool
    intensity: Literal[
        "none",
        "low",
        "medium",
        "high",
    ] | None = None


class HeatMapSeriesResponse(BaseModel):
    name: str
    data: list[HeatMapCellResponse]


class HeatMapLegendResponse(BaseModel):
    min_label: str
    max_label: str
    levels: list[str]


class ActivityHeatMapResponse(BaseModel):
    filter: Literal[
        "all",
        "projects",
        "meetings",
        "workspaces",
    ]

    period: HeatMapPeriodResponse
    summary: HeatMapSummaryResponse
    filters: HeatMapFiltersResponse
    months: list[HeatMapMonthResponse]
    weeks: list[HeatMapWeekResponse]
    weekdays: list[str]
    weekday_totals: dict[str, int]
    days: list[HeatMapDayResponse]
    series: list[HeatMapSeriesResponse]
    legend: HeatMapLegendResponse