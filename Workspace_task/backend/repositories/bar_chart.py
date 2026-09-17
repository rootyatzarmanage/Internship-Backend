from sqlalchemy import func , select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.models.project import Project
from backend.models.workspace import Workspace

class BarChartRepository:
    def __init__(self,session:AsyncSession):
        self.session = session
    async def get_workspace_count(self) -> int :
        result = await self.session.execute(
            select(func.count(Workspace.id)).where(
                Workspace.deleted_at.is_(None)
            )
        )
        return result.scalar_one()
    async def get_project_count(self) -> int :
        result = await self.session.execute(
            select(func.count(Project.id)).where(
                Project.deleted_at.is_(None)
            )
        )
        return result.scalar_one()
    async def get_user_count(self) -> int :
        result = await self.session.execute(
            select(func.count(User.id)).where(
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one()
