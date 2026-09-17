from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.bar_chart import BarChartRepository
from backend.schemas.response.bar_chart import (BarChartData,BarChartResponse)
from backend.services.base import BaseService

class BarChartService(BaseService):
    def __init__(self,session : AsyncSession):
        super().__init__(session)
        self.repo = BarChartRepository(session)

    async def get_chart_data(self) -> BarChartResponse:
        workspace_count = await self.repo.get_workspace_count()
        project_count = await self.repo.get_project_count()
        user_count = await self.repo.get_user_count()
        data = [
            BarChartData(
                label = "Workspace",
                value = workspace_count 
            ),
            BarChartData(
                label = "Project",
                value = project_count
            ),
            BarChartData(
                label= "User",
                value= user_count 
            )
        ]
        return BarChartResponse(data = data)