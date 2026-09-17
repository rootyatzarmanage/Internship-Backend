from fastapi import APIRouter ,status

from backend.core.database.dependencies import DatabaseSession
from backend.core.schemas.responses import SuccessResponse
from backend.schemas.response.forgot_password import ForgotPasswordResponse , ResetPasswordResponse
from backend.schemas.requests.forgot_password import ForgotPasswordRequest , ResetPasswordRequest
from backend.services.forgot_password import ForgotPasswordService 

forgot_router = APIRouter(
    prefix="/forgot-password",
    tags = ["Forgot-Password"]
)

@forgot_router.post(
    "",
    response_model = SuccessResponse[ForgotPasswordResponse],
    status_code = status.HTTP_201_CREATED
)

async def forgot_password(
    body : ForgotPasswordRequest,
    session : DatabaseSession
) -> ForgotPasswordResponse:
    service = ForgotPasswordService(session)
    data = await service.forgot_password(
        body
    )
    return SuccessResponse(
        success= True,
        message= "Password Reset",
        data = data
    )

@forgot_router.post(
    "/reset_password",
    response_model = SuccessResponse[ResetPasswordResponse],
    status_code = status.HTTP_201_CREATED
)

async def reset_password(
    body : ResetPasswordRequest,
    session : DatabaseSession
) -> ResetPasswordResponse:
    service = ForgotPasswordService(session)
    data = await service.reset_password(
        body
    )
    return SuccessResponse(
        success = True,
        message = "Password Reset",
        data = data
    )