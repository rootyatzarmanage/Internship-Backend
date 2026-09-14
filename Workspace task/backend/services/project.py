import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException
from backend.models.project import Project
from backend.repositories.project import ProjectRepository
from backend.repositories.workspace import WorkspaceRepository
from backend.schemas.requests.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
)
from backend.schemas.response.project import ProjectResponse
from backend.services.base import BaseService


class ProjectService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

        self.repo = ProjectRepository(session)
        self.workspace_repo = WorkspaceRepository(session)

    async def create(
        self,
        workspace_id: uuid.UUID,
        body: CreateProjectRequest,
        user_id: uuid.UUID,
    ) -> ProjectResponse:

        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            user_id
        )
        if not workspace:
            raise ConflictException("Workspace not found")
        project = Project(
            name=body.name,
            status=body.status,
            workspace_id=workspace_id,
        )

        project = await self.repo.create(project)
        await self.session.commit()
        await self.session.refresh(project)
        return ProjectResponse.model_validate(project)

    async def get_all(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ProjectResponse]:

        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            user_id
        )
        if not workspace:
            raise ConflictException("Workspace not found")
        projects = await self.repo.get_all_by_workspace(
            workspace_id
        )
        return [
            ProjectResponse.model_validate(project)
            for project in projects
        ]

    async def get_one(
        self,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectResponse:
        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            user_id
        )
        if not workspace:
            raise ConflictException("Workspace not found")
        project = await self.repo.get_by_id(
            project_id,
            workspace_id
        )

        if not project:
            raise ConflictException("Project not found")
        return ProjectResponse.model_validate(project)

    async def update(
        self,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        body: UpdateProjectRequest,
        user_id: uuid.UUID,
    ) -> ProjectResponse:

        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            user_id
        )
        if not workspace:
            raise ConflictException("Workspace not found")
        project = await self.repo.get_by_id(
            project_id,
            workspace_id
        )
        if not project:
            raise ConflictException("Project not found")
        project.name = body.name
        project.status = body.status
        await self.session.commit()
        await self.session.refresh(project)
        return ProjectResponse.model_validate(project)

    async def delete(
        self,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            user_id
        )
        if not workspace:
            raise ConflictException("Workspace not found")
        project = await self.repo.get_by_id(
            project_id,
            workspace_id
        )
        if not project:
            raise ConflictException("Project not found")
        project.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()