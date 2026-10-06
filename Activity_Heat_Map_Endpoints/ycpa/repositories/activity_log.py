import logging
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.audit import AuditLog
from ycpa.models.user import User
from ycpa.models.workspace import (
    AimWorkspace,
    AimWorkspaceMember,
    PimWorkspace,
    PimWorkspaceMember,
)

logger = logging.getLogger(__name__)


ActivityLogFilter = Literal[
    "all",
    "projects",
    "meetings",
    "workspaces",
]


class ActivityLogRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_workspace_ids(
        self,
        user_id: UUID,
    ) -> list[UUID]:

        pim_member_query = select(
            PimWorkspaceMember.workspace_id
        ).where(
            PimWorkspaceMember.user_id == user_id
        )
        aim_member_query = select(
            AimWorkspaceMember.workspace_id
        ).where(
            AimWorkspaceMember.user_id == user_id
        )

        pim_result = await self.session.execute(
            pim_member_query
        )

        aim_result = await self.session.execute(
            aim_member_query
        )

        workspace_ids = {
            row[0]
            for row in pim_result.all()
        }

        workspace_ids.update(
            row[0]
            for row in aim_result.all()
        )

        # Include workspaces owned by the current user.
        pim_owner_query = select(
            PimWorkspace.id
        ).where(
            PimWorkspace.owner_id == user_id
        )

        aim_owner_query = select(
            AimWorkspace.id
        ).where(
            AimWorkspace.owner_id == user_id
        )

        pim_owner_result = await self.session.execute(
            pim_owner_query
        )

        aim_owner_result = await self.session.execute(
            aim_owner_query
        )

        workspace_ids.update(
            row[0]
            for row in pim_owner_result.all()
        )

        workspace_ids.update(
            row[0]
            for row in aim_owner_result.all()
        )

        return list(workspace_ids)

    @staticmethod
    def _category_condition(
        category: ActivityLogFilter,
    ):
        if category == "projects":
            return or_(
                AuditLog.resource_type.ilike("%project%"),
                AuditLog.action.ilike("PROJECT_%"),
            )

        if category == "meetings":
            return or_(
                AuditLog.resource_type.ilike("%meeting%"),
                AuditLog.action.ilike("MEETING_%"),
            )

        if category == "workspaces":
            return or_(
                AuditLog.resource_type.ilike("%workspace%"),
                AuditLog.action.ilike("WORKSPACE_%"),
            )

        return None

    async def get_activity_logs(
        self,
        user_id: UUID,
        category: ActivityLogFilter = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[tuple], int]:

        workspace_ids = await self.get_user_workspace_ids(
            user_id=user_id,
        )

        if not workspace_ids:
            return [], 0

        base_conditions = [
            AuditLog.status == "success",
            AuditLog.workspace_id.in_(workspace_ids),
        ]

        category_condition = self._category_condition(
            category
        )

        if category_condition is not None:
            base_conditions.append(
                category_condition
            )

        count_query = (
            select(AuditLog.id)
            .where(
                and_(*base_conditions)
            )
        )

        count_result = await self.session.execute(
            count_query
        )

        total = len(
            count_result.scalars().all()
        )

        query = (
            select(
                AuditLog,
                User,
            )
            .join(
                User,
                User.id == AuditLog.user_id,
            )
            .where(
                and_(*base_conditions)
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        rows = result.all()

        logger.info(
            "Activity log query completed",
            extra={
                "user_id": str(user_id),
                "category": category,
                "workspace_count": len(workspace_ids),
                "result_count": len(rows),
                "total": total,
            },
        )

        return rows, total