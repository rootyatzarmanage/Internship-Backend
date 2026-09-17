from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.area_chart import AreaChartRepository
from backend.schemas.response.area_chart import (AreaChartData,AreaChartResponse)
from backend.services.base import BaseService

class AreaChartService(BaseService):
    def __init__(self,session : AsyncSession):
        super().__init__(session)
        self.repo = AreaChartRepository(session)

    async def get_chart_data(self) -> AreaChartResponse:
        workspace_count = await self.repo.get_workspace_count()
        project_count = await self.repo.get_project_count()
        user_count = await self.repo.get_user_count()
        data = [
            AreaChartData(
                label = "Workspace",
                value = workspace_count 
            ),
            AreaChartData(
                label = "Project",
                value = project_count
            ),
            AreaChartData(
                label= "User",
                value= user_count 
            )
        ]
        return AreaChartResponse(data = data)