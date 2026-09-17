from fastapi import APIRouter ,status

from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.response.register import RegisterResponse
from backend.schemas.requests.register import RegisterRequest
from backend.services.register import RegisterService

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
