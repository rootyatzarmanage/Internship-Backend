from fastapi import APIRouter ,status

from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.schemas.response.register import RegisterResponse
from ycpa.schemas.requests.register import RegisterRequest
from ycpa.services.register import RegisterService

register_router = APIRouter(
    prefix="/register",
    tags = ["Register"]
)

@register_router.post(
    "",
    response_model = SuccessResponse[RegisterResponse],
    status_code = status.HTTP_201_CREATED
)

async def register(
    body : RegisterRequest,
    session : DatabaseSession
) -> RegisterResponse:
    service = RegisterService(session)
    data = await service.register(
        body
    )
    return SuccessResponse(
        success= True,
        message= "User Registerd Successfully",
        data = data
    )
