from fastapi import APIRouter , Query
from backend.core.auth.dependencies import CurrentUser
from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.response.line_chart import LineChartResponse    
from backend.services.line_chart import LineChartService



line_chart_router = APIRouter(
    prefix="/line_chart",
    tags = ["Line Chart"]
)


@line_chart_router.get(
    "",
    response_model =SuccessResponse[LineChartResponse]
)

async def get_Line_chart(
    session : DatabaseSession,
    currentuser : CurrentUser,
)-> SuccessResponse[LineChartResponse]:
    service = LineChartService(session)
    data = await service.get_chart_data()
    
    return SuccessResponse(
        success=True,
        message= "Line chart data fetched successfully",
        data=data
    )
    
