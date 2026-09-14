import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.project import Project
from backend.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):

    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_all_by_workspace(
        self,
        workspace_id: uuid.UUID
    ) -> list[Project]:

        result = await self.session.execute(
            select(Project).where(
                Project.workspace_id == workspace_id,
                Project.deleted_at.is_(None)
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID
    ) -> Project | None:

        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
                Project.deleted_at.is_(None)
            )
        )

        return result.scalar_one_or_none()