import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.workspace_analytics import (
    WorkspaceAnalyticsRepository,
)
from ycpa.schemas.responses.workspace_analytics import (
    LatestMeetingResponse,
    WorkspaceAnalyticsOverviewResponse,
    DonutChartItem,
    MonthlyPaymentResponse,
    RecentPaymentResponse,
    PaymentAnalyticsResponse
)
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)


class WorkspaceAnalyticsService(BaseService):
    """Workspace analytics operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = WorkspaceAnalyticsRepository(session)

    async def get_workspace_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_workspace_count(
            user_id=user_id,
        )

    async def get_project_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_project_count(
            user_id=user_id,
        )

    async def get_pim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_pim_project_count(
            user_id=user_id,
        )

    async def get_active_pim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_active_pim_project_count(
            user_id=user_id,
        )

    async def get_aim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_aim_project_count(
            user_id=user_id,
        )

    async def get_active_aim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        return await self.repo.get_active_aim_project_count(
            user_id=user_id,
        )

    async def get_latest_meetings(
        self,
        user_id: UUID,
        limit: int = 5,
        search: str | None = None,
    ) -> list[LatestMeetingResponse]:

        meetings = await self.repo.get_latest_meetings(
            user_id=user_id,
            limit=limit,
            search=search,
        )
        response = []
        for meeting in meetings:
            meeting_date = ""
            meeting_time = ""
            if meeting.date:
                parts = meeting.date.split(",", 1)
                meeting_date = parts[0].strip()
                if len(parts) > 1:
                    meeting_time = parts[1].strip()
            response.append(
                LatestMeetingResponse(
                    id=meeting.id,
                    meeting_title=meeting.name,
                    description=meeting.description,
                    date=meeting_date,
                    time=meeting_time,
                    members=(
                        (meeting.member_ids or 0)
                        + (meeting.custom_members or 0)
                    ),
                    groups=meeting.group_ids or 0,
                    status=meeting.status,
                )
            )
        return response

    async def get_overview_chart(
        self,
        user_id: UUID,
    ) -> WorkspaceAnalyticsOverviewResponse:

        workspace_count = await self.get_workspace_count(
            user_id=user_id,
        )

        project_count = await self.get_project_count(
            user_id=user_id,
        )

        pim_project_count = await self.get_pim_project_count(
            user_id=user_id,
        )

        aim_project_count = await self.get_aim_project_count(
            user_id=user_id,
        )

        return WorkspaceAnalyticsOverviewResponse(
            items=[
                DonutChartItem(
                    label="No. of Workspace",
                    value=workspace_count,
                ),
                DonutChartItem(
                    label="No. of Projects",
                    value=project_count,
                ),
                DonutChartItem(
                    label="No. of PIM Projects",
                    value=pim_project_count,
                ),
                DonutChartItem(
                    label="No. of AIM Projects",
                    value=aim_project_count,
                ),
            ],
        )

    async def get_payment_analytics(
        self,
        user_id: UUID,
        year: int,
    ) -> PaymentAnalyticsResponse:

        payment_data = await self.repo.get_payment_analytics(
            user_id=user_id,
            year=year,
        )

        monthly = []
        for month in range(1, 13):
            data = payment_data["monthly"].get(
                month,
                {
                    "pim": 0,
                    "aim": 0,
                },
            )

            pim_amount = data["pim"]
            aim_amount = data["aim"]

            monthly.append(
                MonthlyPaymentResponse(
                    month=month,
                    pim_amount=pim_amount,
                    aim_amount=aim_amount,
                    total_amount=(
                        pim_amount + aim_amount
                    ),
                )
            )

        return PaymentAnalyticsResponse(
            year=payment_data["year"],
            total_amount=payment_data["total_amount"],
            monthly=monthly,
        )

    async def get_recent_payments(
        self,
        user_id: UUID,
        limit: int = 7,
    ) -> list[RecentPaymentResponse]:

        payments = await self.repo.get_recent_payments(
            user_id=user_id,
            limit=limit,
        )

        return [
            RecentPaymentResponse(
                id=payment.id,
                plan=payment.plan,
                product_type=payment.product_type,
                payment_method = payment.payment_method,
                amount=payment.amount,
                billing_period=payment.billing_period,
                status=payment.status,
                payment_date=payment.created_at,
            )
            for payment in payments
        ]