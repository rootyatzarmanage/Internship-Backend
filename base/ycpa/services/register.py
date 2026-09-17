from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.repositories.user import UserRepository
from ycpa.models.user import User
from ycpa.schemas.requests.register import RegisterRequest
from ycpa.schemas.response.register import RegisterResponse
from ycpa.services.base import BaseService
from ycpa.core.exceptions import ConflictException
from ycpa.core.auth.password import get_password_hasher

class RegisterService(BaseService):
    def __init__(self,session:AsyncSession):
        super().__init__(session)
        self.repo = UserRepository(session)
    async def register(
            self,
            body : RegisterRequest
    )-> RegisterResponse:
        if await self.repo.email_exists(body.email):
            raise ConflictException(f"User with {body.email} this email already exist")
        password_hash = get_password_hasher().hash_password(
            body.password
        )
        new_user = User(
            email = body.email,
            password_hash = password_hash,
            full_name = body.full_name,
            is_active = 1
        )
        user = await self.repo.create(
            new_user
        )
        await self.session.commit()
        await self.session.refresh(user)

        return RegisterResponse(
            id = user.id,
            email = user.email,
            full_name = user.full_name,
            is_active = user.is_active
        )

