import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.viewer import IfcMeeting
from ycpa.models.workspace import (
    AimProject,
    AimWorkspace,
    AimWorkspaceMember,
    PimProject,
    PimWorkspace,
    PimWorkspaceMember,
)
from ycpa.models.order import Order

logger = logging.getLogger(__name__)


class WorkspaceAnalyticsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def _pim_workspace_ids(self, user_id: UUID):
        """
        PIM workspaces where the user is:
        - owner
        - workspace admin
        """
        member_workspace_ids = (
            select(PimWorkspaceMember.workspace_id)
            .where(
                PimWorkspaceMember.user_id == user_id,
                PimWorkspaceMember.role == "admin",
            )
        )

        return (
            select(PimWorkspace.id)
            .where(
                PimWorkspace.deleted_at.is_(None),
                or_(
                    PimWorkspace.owner_id == user_id,
                    PimWorkspace.id.in_(member_workspace_ids),
                ),
            )
        )

    def _aim_workspace_ids(self, user_id: UUID):
        """
        AIM workspaces where the user is:
        - owner
        - workspace admin
        """
        member_workspace_ids = (
            select(AimWorkspaceMember.workspace_id)
            .where(
                AimWorkspaceMember.user_id == user_id,
                AimWorkspaceMember.role == "admin",
            )
        )

        return (
            select(AimWorkspace.id)
            .where(
                AimWorkspace.deleted_at.is_(None),
                or_(
                    AimWorkspace.owner_id == user_id,
                    AimWorkspace.id.in_(member_workspace_ids),
                ),
            )
        )

    async def get_workspace_count(
        self,
        user_id: UUID,
    ) -> int:

        pim_workspace_ids = self._pim_workspace_ids(user_id)
        aim_workspace_ids = self._aim_workspace_ids(user_id)

        pim_query = select(
            func.count(PimWorkspace.id)
        ).where(
            PimWorkspace.id.in_(pim_workspace_ids)
        )

        aim_query = select(
            func.count(AimWorkspace.id)
        ).where(
            AimWorkspace.id.in_(aim_workspace_ids)
        )

        pim_count = (
            await self.session.execute(pim_query)
        ).scalar() or 0

        aim_count = (
            await self.session.execute(aim_query)
        ).scalar() or 0

        return pim_count + aim_count

    async def get_project_count(
        self,
        user_id: UUID,
    ) -> int:

        pim_workspace_ids = self._pim_workspace_ids(user_id)
        aim_workspace_ids = self._aim_workspace_ids(user_id)

        pim_query = select(
            func.count(PimProject.id)
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.workspace_id.in_(pim_workspace_ids),
        )

        aim_query = select(
            func.count(AimProject.id)
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.workspace_id.in_(aim_workspace_ids),
        )

        pim_count = (
            await self.session.execute(pim_query)
        ).scalar() or 0

        aim_count = (
            await self.session.execute(aim_query)
        ).scalar() or 0

        return pim_count + aim_count

    async def get_pim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        pim_workspace_ids = self._pim_workspace_ids(user_id)

        query = select(
            func.count(PimProject.id)
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.workspace_id.in_(pim_workspace_ids),
        )

        return (
            await self.session.execute(query)
        ).scalar() or 0

    async def get_active_pim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        pim_workspace_ids = self._pim_workspace_ids(user_id)

        query = select(
            func.count(PimProject.id)
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.status == "active",
            PimProject.workspace_id.in_(pim_workspace_ids),
        )

        return (
            await self.session.execute(query)
        ).scalar() or 0


    async def get_aim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        aim_workspace_ids = self._aim_workspace_ids(user_id)

        query = select(
            func.count(AimProject.id)
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.workspace_id.in_(aim_workspace_ids),
        )

        return (
            await self.session.execute(query)
        ).scalar() or 0

    async def get_active_aim_project_count(
        self,
        user_id: UUID,
    ) -> int:

        aim_workspace_ids = self._aim_workspace_ids(user_id)

        query = select(
            func.count(AimProject.id)
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.status == "active",
            AimProject.workspace_id.in_(aim_workspace_ids),
        )

        return (
            await self.session.execute(query)
        ).scalar() or 0

    async def get_latest_meetings(
        self,
        user_id: UUID,
        limit: int = 5,
        search: str | None = None,
    ) -> list[IfcMeeting]:

        pim_workspace_ids = self._pim_workspace_ids(user_id)
        aim_workspace_ids = self._aim_workspace_ids(user_id)

        pim_project_ids = select(
            PimProject.id
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.workspace_id.in_(pim_workspace_ids),
        )

        aim_project_ids = select(
            AimProject.id
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.workspace_id.in_(aim_workspace_ids),
        )

        query = (
            select(IfcMeeting)
            .where(
                or_(
                    (
                        (IfcMeeting.owner_type == "ADMIN")
                        & (IfcMeeting.owner_id == user_id)
                    ),
                    (
                        (IfcMeeting.owner_type == "PIM_WORKSPACE")
                        & IfcMeeting.owner_id.in_(pim_workspace_ids)
                    ),
                    (
                        (IfcMeeting.owner_type == "AIM_WORKSPACE")
                        & IfcMeeting.owner_id.in_(aim_workspace_ids)
                    ),
                    (
                        (IfcMeeting.owner_type == "PIM_PROJECT")
                        & IfcMeeting.owner_id.in_(pim_project_ids)
                    ),
                    (
                        (IfcMeeting.owner_type == "AIM_PROJECT")
                        & IfcMeeting.owner_id.in_(aim_project_ids)
                    ),
                )
            )
            .order_by(
                IfcMeeting.created_at.desc()
            )
            .limit(limit)
        )

        if search:
            query = query.where(
                IfcMeeting.name.ilike(
                    f"%{search.strip()}%"
                )
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_payment_analytics(
        self,
        user_id: UUID,
        year: int,
    ) -> dict:

        query = (
            select(
                func.extract(
                    "month",
                    Order.created_at,
                ).label("month"),
                Order.product_type,
                func.sum(Order.amount).label("total"),
            )
            .where(
                Order.user_id == user_id,
                Order.status == "paid",
                func.extract(
                    "year",
                    Order.created_at,
                ) == year,
            )
            .group_by(
                func.extract(
                    "month",
                    Order.created_at,
                ),
                Order.product_type,
            )
            .order_by(
                func.extract(
                    "month",
                    Order.created_at,
                )
            )
        )

        result = await self.session.execute(query)

        monthly = {}

        for row in result.all():

            month = int(row.month)

            if month not in monthly:
                monthly[month] = {
                    "pim": 0,
                    "aim": 0,
                }

            product_type = (
                str(row.product_type)
                .lower()
                .strip()
            )

            amount = int(row.total or 0)

            if "pim" in product_type:
                monthly[month]["pim"] += amount

            elif "aim" in product_type:
                monthly[month]["aim"] += amount

        total_query = (
            select(
                func.coalesce(
                    func.sum(Order.amount),
                    0,
                )
            )
            .where(
                Order.user_id == user_id,
                Order.status == "paid",
                func.extract(
                    "year",
                    Order.created_at,
                ) == year,
            )
        )

        total_amount = (
            await self.session.execute(total_query)
        ).scalar() or 0

        return {
            "year": year,
            "total_amount": int(total_amount),
            "monthly": monthly,
        }

    async def get_recent_payments(
        self,
        user_id: UUID,
        limit: int = 7,
    ) -> list[Order]:

        query = (
            select(Order)
            .where(
                Order.user_id == user_id,
                Order.status == "paid",
            )
            .order_by(
                Order.created_at.desc()
            )
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

