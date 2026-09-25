import logging
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.workspace import (
    AimProject,
    AimWorkspace,
    AimWorkspaceMember,
    PimProject,
    PimWorkspace,
    PimWorkspaceMember
)

logger = logging.getLogger(__name__)

class WorkspaceOverviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_workspaces( 
        self,
        user_id: UUID,
        filter_type: str = "all"
    ) -> list[dict]:
        workspaces = [] 
        pim_owner_query = select(PimWorkspace).where(
            PimWorkspace.owner_id == user_id,
            PimWorkspace.deleted_at.is_(None)
        )
        pim_shared_query = (select(PimWorkspace).join(
            PimWorkspaceMember,
            PimWorkspaceMember.workspace_id == PimWorkspace.id
        ).where(
            PimWorkspaceMember.user_id == user_id,
            PimWorkspace.deleted_at.is_(None),
            PimWorkspace.owner_id != user_id
            )
        )
        aim_owner_query = select(AimWorkspace).where(
            AimWorkspace.owner_id == user_id,
            AimWorkspace.deleted_at.is_(None)
        )
        aim_shared_query = (select(AimWorkspace).join(
            AimWorkspaceMember,
            AimWorkspaceMember.user_id == user_id,
        ).where(
            AimWorkspaceMember.user_id == user_id,
            AimWorkspace.deleted_at.is_(None),
            AimWorkspace.owner_id != user_id
            )
        )
        if filter_type == "my_workspace":
            pim_result = await self.session.execute(pim_owner_query)
            aim_result = await self.session.execute(aim_owner_query)
            pim_workspaces = pim_result.scalars().all()
            aim_workspaces = aim_result.scalars().all()
            for workspace in pim_workspaces:
               workspaces.append(
                   {
                       "workspace": workspace,
                       "role": "owner"
                   }
               )
            for workspace in aim_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "owner"
                    }
                )

        elif filter_type == "shared":
            pim_result = await self.session.execute(pim_shared_query)
            aim_result = await self.session.execute(aim_shared_query)
            pim_workspaces = pim_result.scalars().all()
            aim_workspaces = aim_result.scalars().all()

            for workspace in pim_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "member",
                    }
                )

            for workspace in aim_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "member",
                    }
                )
        else:
            pim_owner_result = await self.session.execute(pim_owner_query)
            pim_shared_result = await self.session.execute(pim_shared_query)
            aim_owner_result = await self.session.execute(aim_owner_query)
            aim_shared_result = await self.session.execute(aim_shared_query)
            pim_owner_workspaces = pim_owner_result.scalars().all()
            pim_shared_workspaces = pim_shared_result.scalars().all()
            aim_owner_workspaces = aim_owner_result.scalars().all()
            aim_shared_workspaces = aim_shared_result.scalars().all()   
            for workspace in pim_owner_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "owner",
                    }
                )
            for workspace in pim_shared_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "member",
                    }
                )
            for workspace in aim_owner_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "owner",
                    }
                )
            for workspace in aim_shared_workspaces:
                workspaces.append(
                    {
                        "workspace": workspace,
                        "role": "member",
                    }
                )
        return await self._attach_projects(workspaces)
    
    async def _attach_projects(
        self,
        workspaces: list[dict],
    ) -> list[dict]:

        result = []

        for item in workspaces:
            workspace = item["workspace"]

            # Dynamically infer the type based on the SQLAlchemy model class
            if isinstance(workspace, PimWorkspace):
                project_query = (
                    select(PimProject)
                    .where(
                        PimProject.workspace_id == workspace.id,
                        PimProject.deleted_at.is_(None),
                    )
                    .order_by(PimProject.created_at.desc())
                )
            else:
                project_query = (
                    select(AimProject)
                    .where(
                        AimProject.workspace_id == workspace.id,
                        AimProject.deleted_at.is_(None),
                    )
                    .order_by(AimProject.created_at.desc())
                )

            project_result = await self.session.execute(project_query)
            projects = project_result.scalars().all()

            result.append(
                {
                    "workspace": workspace,
                    "role": item["role"],
                    "projects": projects,
                }
            )

        return result
