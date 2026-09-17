from fastapi import APIRouter , Query
from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.response.area_chart import AreaChartResponse    
from backend.services.area_chart import AreaChartService



area_chart_router = APIRouter(
    prefix="/area_chart",
    tags = ["Area Chart"]
)


@area_chart_router.get(
    "",
    response_model =SuccessResponse[AreaChartResponse]
)

async def get_Area_chart(
    session : DatabaseSession,
    currentuser : CurrentUser,
)-> SuccessResponse[AreaChartResponse]:
    service = AreaChartService(session)
    data = await service.get_chart_data()
    
    return SuccessResponse(
        success=True,
        message= "Area chart data fetched successfully",
        data=data
    )
    
