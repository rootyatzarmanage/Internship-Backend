import logging
 
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
 
from ycpa.core.auth.dependencies import (
    ACCESS_TOKEN_COOKIE,
    ID_TOKEN_COOKIE,
    CurrentUser,
)
from ycpa.core.config import get_settings
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.database.session import get_async_session
from ycpa.core.schemas.responses import SuccessResponse
from ycpa.models.platform_permission import UserPlatformPermission
from ycpa.schemas.requests.auth import LoginRequest
from ycpa.schemas.responses.auth import LoginResponse, UserProfileResponse
from ycpa.services.auth import AuthService
from ycpa.services.cde import CdeService
 
logger = logging.getLogger(__name__)
settings = get_settings()
 
router = APIRouter(prefix="/auth", tags=["Auth"])
 
COOKIE_SECURE   = settings.ENVIRONMENT not in ("local", "development")
COOKIE_SAMESITE = "none" if settings.ENVIRONMENT not in ("local", "development") else "lax"
COOKIE_MAX_AGE  = 60 * 60
 
 
@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    session: DatabaseSession,
) -> SuccessResponse[LoginResponse]:
    service = AuthService(session)
    result = await service.login(
        id_token=body.id_token,
        ip_address=_get_ip(request),
    )
 
    cde_service = CdeService(session)
 
    if result.is_new_user:
        await cde_service.seed_sample_file(result.user)
        logger.info("Sample file seeded", extra={"user_id": str(result.user.id)})
 
    try:
        attached = await cde_service.attach_pending_shares_for_user(
            email=result.user.email,
            user_id=result.user.id,
        )
        if attached:
            logger.info(
                "Pending CDE shares attached",
                extra={"user_id": str(result.user.id), "count": attached},
            )
    except Exception as exc:
        logger.error(
            "Failed to attach pending CDE shares — non-fatal",
            extra={"user_id": str(result.user.id), "error": str(exc)},
            exc_inc=True,
        )
 
    await session.commit()
 
    _set_cookies(response, body.id_token, body.access_token)
    return SuccessResponse(
        success=True,
        message="Welcome to ycpa!" if result.is_new_user else "Welcome back!",
        data=result,
    )
 
 
@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> SuccessResponse:
    service = AuthService(session)
    await service.logout(user=current_user, ip_address=_get_ip(request))
    _clear_cookies(response)
    return SuccessResponse(success=True, message="Logged out successfully.")
 
 
@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
)
async def get_me(
    current_user: CurrentUser,
    session=Depends(get_async_session),
) -> SuccessResponse[UserProfileResponse]:
    try:
        result = await session.execute(
            select(UserPlatformPermission.permission_slug).where(
                UserPlatformPermission.user_id == current_user.id
            )
        )
        permissions = [row[0] for row in result.all()]
    except Exception:
        permissions = []
 
    profile = UserProfileResponse.model_validate(current_user)
    profile.platform_permissions = permissions
 
    return SuccessResponse(
        success=True,
        message="Profile retrieved.",
        data=profile,
    )
 
 
def _set_cookies(response: Response, id_token: str, access_token: str) -> None:
    _args = {
        "httponly": True,
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE,
        "max_age": COOKIE_MAX_AGE,
        "path": "/",
    }
    response.set_cookie(key=ID_TOKEN_COOKIE,     value=id_token,     **_args)
    response.set_cookie(key=ACCESS_TOKEN_COOKIE, value=access_token, **_args)
 
 
def _clear_cookies(response: Response) -> None:
    _args = {"httponly": True, "secure": COOKIE_SECURE, "samesite": COOKIE_SAMESITE, "path": "/"}
    response.delete_cookie(key=ID_TOKEN_COOKIE,     **_args)
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, **_args)
 
 
def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

 