import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.workspace import PimWorkspace  
from ycpa.repositories.workspace_overview import (
    WorkspaceOverviewRepository,
)

from ycpa.schemas.responses.workspace_overview import (
    WorkspaceOverviewItemResponse,
    WorkspaceOverviewResponse,
    WorkspaceProjectResponse,
)

from ycpa.services.base import BaseService


logger = logging.getLogger(__name__)


class WorkspaceOverviewService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = WorkspaceOverviewRepository(session)

    async def get_workspace_overview(
        self,
        user_id: UUID,
        filter_type: str = "all",
    ) -> WorkspaceOverviewResponse:

        workspace_data = await self.repo.get_workspaces(
            user_id=user_id,
            filter_type=filter_type,
        )

        workspaces = []

        for item in workspace_data:
            workspace = item["workspace"]
            resolved_type = "PIM" if isinstance(workspace, PimWorkspace) else "AIM"
            
            projects = []
            for project in item["projects"]:
                projects.append(
                    WorkspaceProjectResponse(
                        id=project.id,
                        name=project.name,
                        description=project.description,
                        project_type=resolved_type,  
                        created_at=(
                            project.created_at.date()
                            if project.created_at
                            else None
                        ),
                    )
                )

            workspaces.append(
                WorkspaceOverviewItemResponse(
                    id=workspace.id,
                    name=workspace.name,
                    role=item["role"],
                    project_count=len(projects),
                    projects=projects,
                )
            )

        return WorkspaceOverviewResponse(
            workspaces=workspaces,
            total_workspaces=len(workspaces),
        )
