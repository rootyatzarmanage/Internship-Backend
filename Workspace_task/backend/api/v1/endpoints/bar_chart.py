from fastapi import APIRouter , Query
from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.response.bar_chart import BarChartResponse    
from backend.services.bar_chart import BarChartService



bar_chart_router = APIRouter(
    prefix="/bar_chart",
    tags = ["Bar Chart"]
)


@bar_chart_router.get(
    "",
    response_model =SuccessResponse[BarChartResponse]
)

async def get_Line_chart(
    session : DatabaseSession,
    currentuser : CurrentUser,
)-> SuccessResponse[BarChartResponse]:
    service = BarChartService(session)
    data = await service.get_chart_data()
    
    return SuccessResponse(
        success=True,
        message= "Line chart data fetched successfully",
        data=data
    )
    
