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

logger = logging.getLogger(__name__)


class WorkspaceAnalyticsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def _pim_workspace_ids(self, user_id: UUID):
        """
        Workspaces where the user is:
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
        Workspaces where the user is:
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

    async def get_workspace_counts(
        self,
        user_id: UUID,
    ) -> dict:
        pim_workspace_ids = self._pim_workspace_ids(user_id)
        aim_workspace_ids = self._aim_workspace_ids(user_id)
        pim_workspace_count_query = select(
            func.count(PimWorkspace.id)
        ).where(
            PimWorkspace.id.in_(pim_workspace_ids)
        )
        aim_workspace_count_query = select(
            func.count(AimWorkspace.id)
        ).where(
            AimWorkspace.id.in_(aim_workspace_ids)
        )
        pim_project_count_query = select(
            func.count(PimProject.id)
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.workspace_id.in_(pim_workspace_ids),
        )
        aim_project_count_query = select(
            func.count(AimProject.id)
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.workspace_id.in_(aim_workspace_ids),
        )
        pim_active_project_count_query = select(
            func.count(PimProject.id)
        ).where(
            PimProject.deleted_at.is_(None),
            PimProject.status == "active",
            PimProject.workspace_id.in_(pim_workspace_ids),
        )
        aim_active_project_count_query = select(
            func.count(AimProject.id)
        ).where(
            AimProject.deleted_at.is_(None),
            AimProject.status == "active",
            AimProject.workspace_id.in_(aim_workspace_ids),
        )
        pim_workspace_count = (
            await self.session.execute(pim_workspace_count_query)
        ).scalar() or 0
        aim_workspace_count = (
            await self.session.execute(aim_workspace_count_query)
        ).scalar() or 0
        pim_project_count = (
            await self.session.execute(pim_project_count_query)
        ).scalar() or 0
        aim_project_count = (
            await self.session.execute(aim_project_count_query)
        ).scalar() or 0
        pim_active_project_count = (
            await self.session.execute(
                pim_active_project_count_query
            )
        ).scalar() or 0
        aim_active_project_count = (
            await self.session.execute(
                aim_active_project_count_query
            )
        ).scalar() or 0
        return {
            "pim_workspace_count": pim_workspace_count,
            "aim_workspace_count": aim_workspace_count,
            "workspace_count": (
                pim_workspace_count + aim_workspace_count
            ),
            "pim_project_count": pim_project_count,
            "aim_project_count": aim_project_count,
            "project_count": (
                pim_project_count + aim_project_count
            ),
            "pim_active_project_count": pim_active_project_count,
            "aim_active_project_count": aim_active_project_count,
        }
    
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
                    # Admin-owned meetings
                    (
                        (IfcMeeting.owner_type == "ADMIN")
                        & (IfcMeeting.owner_id == user_id)
                    ),

                    # PIM workspace-owned meetings
                    (
                        (IfcMeeting.owner_type == "PIM_WORKSPACE")
                        & IfcMeeting.owner_id.in_(pim_workspace_ids)
                    ),

                    # AIM workspace-owned meetings
                    (
                        (IfcMeeting.owner_type == "AIM_WORKSPACE")
                        & IfcMeeting.owner_id.in_(aim_workspace_ids)
                    ),

                    # PIM project-owned meetings
                    (
                        (IfcMeeting.owner_type == "PIM_PROJECT")
                        & IfcMeeting.owner_id.in_(pim_project_ids)
                    ),

                    # AIM project-owned meetings
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