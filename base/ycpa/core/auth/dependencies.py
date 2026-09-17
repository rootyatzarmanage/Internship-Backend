import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends
from ycpa.core.auth.jwt_verifier import get_jwt_generator
from ycpa.core.database.dependencies import DatabaseSession
from ycpa.core.exceptions import ForbiddenException, UnauthorizedException
from ycpa.models.user import User
from ycpa.repositories.user import UserRepository

logger = logging.getLogger(__name__)

ID_TOKEN_COOKIE = "ycpa_id_token"


async def get_current_user(
    session: DatabaseSession,
    ycpa_id_token: Optional[str] = Cookie(default=None, alias=ID_TOKEN_COOKIE),
) -> User:

    if not ycpa_id_token:
        raise UnauthorizedException("Authentication required")

    try:
        user_id = get_jwt_generator().verify_access_token(ycpa_id_token)
    except Exception as e:
        logger.warning("JWT verification failed", extra={"error": str(e)})
        raise UnauthorizedException("Session expired. Please sign in again.")

    if not user_id:
        raise UnauthorizedException("Invalid token claims")

    repo = UserRepository(session)
    user = await repo.get_by_id(UUID(user_id))

    if not user:
        raise UnauthorizedException("User not found. Please sign in again.")
    if not user.is_active:
        raise ForbiddenException("Your account has been deactivated.")
    if user.deleted_at is not None:
        raise ForbiddenException("Account no longer exists.")

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_optional_user(
    session: DatabaseSession,
    ycpa_id_token: Optional[str] = Cookie(default=None, alias=ID_TOKEN_COOKIE),
) -> Optional[User]:
    if not ycpa_id_token:
        return None
    try:
        return await get_current_user(session, ycpa_id_token)
    except Exception:
        return None

OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
