from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

class ProjectCountResponse(BaseModel):
    total_count: int
    active_count: int

class CountResponse(BaseModel):
    count: int

class DonutChartItem(BaseModel):
    label : str
    value : int

class WorkspaceAnalyticsOverviewResponse(BaseModel):
    items : list[DonutChartItem]

class LatestMeetingResponse(BaseModel):
    id: UUID
    meeting_title: str
    description: str | None
    date: str
    time: str
    members: int
    groups: int
    status: str

class MonthlyPaymentResponse(BaseModel):
    month: int
    pim_amount: int
    aim_amount: int
    total_amount: int


class PaymentAnalyticsResponse(BaseModel):
    year: int
    total_amount: int
    monthly: list[MonthlyPaymentResponse]


class RecentPaymentResponse(BaseModel):
    id: UUID
    plan: str
    product_type: str
    payment_method : str | None
    amount: int
    billing_period: str
    status: str
    payment_date: datetime