from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.auth.jwt_verifier import get_jwt_generator
from ycpa.repositories.user import UserRepository
from ycpa.schemas.requests.auth import LoginRequest
from ycpa.schemas.response.auth import LoginResponse
from ycpa.services.base import BaseService
from ycpa.core.exceptions import UnauthorizedException
from ycpa.core.auth.password import get_password_hasher

class AuthService(BaseService):
    def __init__(self,session:AsyncSession):
        super().__init__(session)
        self.repo = UserRepository(session)
    async def Auth(
            self,
            body : LoginRequest
    )-> LoginResponse:
        user = await self.repo.get_by_email(
            body.email
        )
        if not user:
            raise UnauthorizedException(
                "User not registered"
            )
        if not get_password_hasher().verify_password(
            body.password,
            user.password_hash
        ):
            raise UnauthorizedException(
                "Invalid email or password"
            )
        if not user.is_active:
            raise UnauthorizedException(
                "User is inactive"
            )
        access_token = get_jwt_generator().create_access_token(
            str(user.id)
        )

        return LoginResponse(
            access_token = access_token,
            token_type = "bearer"
        )