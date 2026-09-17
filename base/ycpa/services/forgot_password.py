from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.user import UserRepository
from ycpa.models.user import User
from ycpa.schemas.requests.forgot_password import ForgotPasswordRequest , ResetPasswordRequest
from ycpa.schemas.response.forgot_password import ForgotPasswordResponse , ResetPasswordResponse
from ycpa.services.base import BaseService
from ycpa.core.exceptions import ConflictException , UnauthorizedException
from ycpa.core.auth.jwt_verifier import get_jwt_generator 
from ycpa.core.auth.password import get_password_hasher

class ForgotPasswordService(BaseService):
    def __init__(self,session:AsyncSession):
        super().__init__(session)
        self.repo = UserRepository(session)

    async def forgot_password(
        self,
        body : ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        user = await self.repo.get_by_email(
        body.email
        )

        if not user:
            raise UnauthorizedException(
                "User not registered"
            )

        reset_token = get_jwt_generator().create_reset_token(
            str(user.id)
        )

        return ForgotPasswordResponse(
            message = "Password reset token generated successfully",
            reset_token = reset_token
        )

    async def reset_password(
        self,
        body: ResetPasswordRequest
    ) -> ResetPasswordResponse:

        user_id = get_jwt_generator().verify_reset_token(
          body.reset_token
        )
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException(
                "User not registered"
            )

        new_password_hash = get_password_hasher().hash_password(
            body.new_password
        )
        user.password_hash = new_password_hash

        await self.session.commit()
        await self.session.refresh(user)

        return ResetPasswordResponse(
            message="Password reset successfully"
        )