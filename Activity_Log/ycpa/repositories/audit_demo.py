from uuid import UUID

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.workspace import PimWorkspace, PimProject
from ycpa.models.audit import AuditLog


class AuditDemoRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_workspace(
        self,
        workspace: PimWorkspace,
    ) -> PimWorkspace:
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def get_workspace(
        self,
        workspace_id: UUID,
    ) -> PimWorkspace | None:
        return await self.session.get(
            PimWorkspace,
            workspace_id,
        )

    async def create_project(
        self,
        project: PimProject,
    ) -> PimProject:
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_activity_logs(
        self,
        user_id: UUID,
        workspace_id: UUID | None,
        limit: int,
        offset: int,
    ):
        query = select(AuditLog).where(
            AuditLog.user_id == user_id
        )

        count_query = select(func.count()).select_from(
            AuditLog
        ).where(
            AuditLog.user_id == user_id
        )

        if workspace_id:
            query = query.where(
                AuditLog.workspace_id == workspace_id
            )
            count_query = count_query.where(
                AuditLog.workspace_id == workspace_id
            )

        query = query.order_by(
            desc(AuditLog.created_at),
            desc(AuditLog.id),
        )

        result = await self.session.scalars(
            query.limit(limit).offset(offset)
        )

        total = await self.session.scalar(count_query)

        return result.all(), total or 0