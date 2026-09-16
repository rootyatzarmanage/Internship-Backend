from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.line_chart import LineChartRepository
from backend.schemas.response.line_chart import (LineChartData,LineChartResponse)
from backend.services.base import BaseService

class LineChartService(BaseService):
    def __init__(self,session : AsyncSession):
        super().__init__(session)
        self.repo = LineChartRepository(session)

    async def get_chart_data(self) -> LineChartResponse:
        workspace_count = await self.repo.get_workspace_count()
        project_count = await self.repo.get_project_count()
        user_count = await self.repo.get_user_count()
        data = [
            LineChartData(
                label = "Workspace",
                value = workspace_count 
            ),
            LineChartData(
                label = "Project",
                value = project_count
            ),
            LineChartData(
                label= "User",
                value= user_count 
            )
        ]
        return LineChartResponse(data = data)