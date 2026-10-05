import logging
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import Date, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.audit import AuditLog
from ycpa.models.workspace import (
    AimProject,
    AimProjectMember,
    AimWorkspace,
    AimWorkspaceMember,
    PimProject,
    PimProjectMember,
    PimWorkspace,
    PimWorkspaceMember,
)


logger = logging.getLogger(__name__)


HeatMapFilter = Literal[
    "all",
    "projects",
    "meetings",
    "workspaces",
]


PROJECT_RESOURCE_TYPES = (
    "project",
    "pim_project",
    "aim_project",
)

WORKSPACE_RESOURCE_TYPES = (
    "workspace",
    "pim_workspace",
    "aim_workspace",
)

MEETING_RESOURCE_TYPES = (
    "meeting",
    "meetings",
    "ifc_meeting",
)


class ActivityHeatMapRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    def _get_accessible_workspace_ids(
        self,
        user_id: UUID,
    ):
        pim_workspace_ids = (
            select(PimWorkspace.id)
            .where(
                PimWorkspace.deleted_at.is_(None),
                or_(
                    PimWorkspace.owner_id == user_id,
                    PimWorkspace.id.in_(
                        select(
                            PimWorkspaceMember.workspace_id
                        ).where(
                            PimWorkspaceMember.user_id
                            == user_id
                        )
                    ),
                ),
            )
        )

        aim_workspace_ids = (
            select(AimWorkspace.id)
            .where(
                AimWorkspace.deleted_at.is_(None),
                or_(
                    AimWorkspace.owner_id == user_id,
                    AimWorkspace.id.in_(
                        select(
                            AimWorkspaceMember.workspace_id
                        ).where(
                            AimWorkspaceMember.user_id
                            == user_id
                        )
                    ),
                ),
            )
        )

        return (
            pim_workspace_ids,
            aim_workspace_ids,
        )

    def _get_accessible_project_ids(
        self,
        user_id: UUID,
        pim_workspace_ids,
        aim_workspace_ids,
    ):
        pim_project_ids = (
            select(PimProject.id)
            .where(
                PimProject.deleted_at.is_(None),
                or_(
                    PimProject.created_by == user_id,

                    PimProject.workspace_id.in_(
                        pim_workspace_ids
                    ),

                    PimProject.id.in_(
                        select(
                            PimProjectMember.project_id
                        ).where(
                            PimProjectMember.user_id
                            == user_id
                        )
                    ),
                ),
            )
        )

        aim_project_ids = (
            select(AimProject.id)
            .where(
                AimProject.deleted_at.is_(None),
                or_(
                    AimProject.created_by == user_id,

                    AimProject.workspace_id.in_(
                        aim_workspace_ids
                    ),

                    AimProject.id.in_(
                        select(
                            AimProjectMember.project_id
                        ).where(
                            AimProjectMember.user_id
                            == user_id
                        )
                    ),
                ),
            )
        )

        return (
            pim_project_ids,
            aim_project_ids,
        )

    @staticmethod
    def _category_condition(
        category: HeatMapFilter,
    ):
        if category == "projects":
            return or_(
                func.lower(
                    AuditLog.resource_type
                ).in_(
                    PROJECT_RESOURCE_TYPES
                ),

                func.upper(
                    AuditLog.action
                ).like(
                    "PROJECT_%"
                ),
            )

        if category == "workspaces":
            return or_(
                func.lower(
                    AuditLog.resource_type
                ).in_(
                    WORKSPACE_RESOURCE_TYPES
                ),

                func.upper(
                    AuditLog.action
                ).like(
                    "WORKSPACE_%"
                ),
            )

        if category == "meetings":
            return or_(
                func.lower(
                    AuditLog.resource_type
                ).in_(
                    MEETING_RESOURCE_TYPES
                ),

                func.upper(
                    AuditLog.action
                ).like(
                    "MEETING_%"
                ),
            )

        return None

    async def get_daily_activity_counts(
        self,
        user_id: UUID,
        start_utc: datetime,
        end_utc: datetime,
        timezone_name: str,
        category: HeatMapFilter = "all",
    ) -> dict[date, int]:

        (
            pim_workspace_ids,
            aim_workspace_ids,
        ) = self._get_accessible_workspace_ids(
            user_id
        )

        (
            pim_project_ids,
            aim_project_ids,
        ) = self._get_accessible_project_ids(
            user_id,
            pim_workspace_ids,
            aim_workspace_ids,
        )

        accessible_workspace_ids = (
            select(PimWorkspace.id)
            .where(
                PimWorkspace.id.in_(
                    pim_workspace_ids
                )
            )
            .union_all(
                select(AimWorkspace.id)
                .where(
                    AimWorkspace.id.in_(
                        aim_workspace_ids
                    )
                )
            )
        )

        accessible_project_ids = (
            select(PimProject.id)
            .where(
                PimProject.id.in_(
                    pim_project_ids
                )
            )
            .union_all(
                select(AimProject.id)
                .where(
                    AimProject.id.in_(
                        aim_project_ids
                    )
                )
            )
        )

        activity_date = cast(
            func.timezone(
                timezone_name,
                AuditLog.created_at,
            ),
            Date,
        ).label(
            "activity_date"
        )

        query = (
            select(
                activity_date,
                func.count(
                    AuditLog.id
                ).label(
                    "activity_count"
                ),
            )
            .where(
                AuditLog.created_at >= start_utc,

                AuditLog.created_at < end_utc,

                AuditLog.status == "success",

                or_(
                    AuditLog.user_id == user_id,

                    AuditLog.workspace_id.in_(
                        accessible_workspace_ids
                    ),

                    AuditLog.project_id.in_(
                        accessible_project_ids
                    ),
                ),
            )
        )

        category_condition = (
            self._category_condition(
                category
            )
        )

        if category_condition is not None:
            query = query.where(
                category_condition
            )

        query = (
            query
            .group_by(activity_date)
            .order_by(activity_date)
        )

        result = await self.session.execute(
            query
        )

        rows = result.all()

        return {
            row.activity_date: int(
                row.activity_count
            )
            for row in rows
            if row.activity_date is not None
        }