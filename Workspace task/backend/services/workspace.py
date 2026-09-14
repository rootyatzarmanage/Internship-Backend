import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException
from backend.models.workspace import Workspace
from backend.repositories.workspace import WorkspaceRepository
from backend.schemas.requests.workspace import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
)
from backend.schemas.response.workspace import WorkspaceResponse
from backend.services.base import BaseService


class WorkspaceService(BaseService):

    def __init__(
        self,
        session: AsyncSession
    ):
        super().__init__(session)

        self.repo = WorkspaceRepository(session)

    async def create(
        self,
        body: CreateWorkspaceRequest,
        user_id: uuid.UUID
    ) -> WorkspaceResponse:

        workspace = Workspace(
            name=body.name,
            status=body.status,
            user_id=user_id
        )

        workspace = await self.repo.create(workspace)

        await self.session.commit()
        await self.session.refresh(workspace)

        return WorkspaceResponse.model_validate(workspace)

    async def get_all(
        self,
        user_id: uuid.UUID
    ) -> list[WorkspaceResponse]:

        workspaces = await self.repo.get_all_by_user(
            user_id
        )

        return [
            WorkspaceResponse.model_validate(workspace)
            for workspace in workspaces
        ]

    async def get_one(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> WorkspaceResponse:

        workspace = await self.repo.get_by_id(
            workspace_id,
            user_id
        )

        if not workspace:
            raise ConflictException(
                "Workspace not found"
            )

        return WorkspaceResponse.model_validate(workspace)

    async def update(
        self,
        workspace_id: uuid.UUID,
        body: UpdateWorkspaceRequest,
        user_id: uuid.UUID
    ) -> WorkspaceResponse:

        workspace = await self.repo.get_by_id(
            workspace_id,
            user_id
        )

        if not workspace:
            raise ConflictException(
                "Workspace not found"
            )

        workspace.name = body.name
        workspace.status = body.status

        await self.session.commit()
        await self.session.refresh(workspace)

        return WorkspaceResponse.model_validate(workspace)

    async def delete(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:

        workspace = await self.repo.get_by_id(
            workspace_id,
            user_id
        )

        if not workspace:
            raise ConflictException(
                "Workspace not found"
            )

        workspace.deleted_at = datetime.now(
            timezone.utc
        )

        await self.session.commit()