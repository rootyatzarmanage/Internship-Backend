from fastapi import APIRouter ,status, Response

from backend.core.database.dependencies import DatabaseSession
from backend.schemas.requests.auth import LoginRequest
from backend.schemas.response.auth import LoginResponse
from backend.core.schemas.responses import SuccessResponse
from backend.services.auth import AuthService

auth_router = APIRouter(
    prefix="/auth",
    tags = ["Auth"]
)

@auth_router.post(
    "/login",
    response_model = SuccessResponse[LoginResponse],
    status_code = status.HTTP_200_OK   
)
async def login(
    body : LoginRequest,
    session : DatabaseSession,
    response : Response
) ->  LoginResponse:
    service = AuthService(session)
    data = await service.Auth(
        body
    )
    response.set_cookie(
        key="ycpa_id_token",
        value=data.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60
    )
    return SuccessResponse(
        success = True,
        message = "Login Successfully",
        data = data 
    )


