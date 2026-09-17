import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.workspace import Workspace
from backend.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):

    def __init__(
        self,
        session: AsyncSession
    ):
        super().__init__(
            Workspace,
            session
        )

    async def get_all_by_user(
        self,
        user_id: uuid.UUID
    ) -> list[Workspace]:

        result = await self.session.execute(
            select(Workspace).where(
                Workspace.user_id == user_id,
                Workspace.deleted_at.is_(None)
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Workspace | None:

        result = await self.session.execute(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.user_id == user_id,
                Workspace.deleted_at.is_(None)
            )
        )

        return result.scalar_one_or_none()