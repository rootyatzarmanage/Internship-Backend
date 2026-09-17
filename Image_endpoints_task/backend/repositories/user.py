import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User
from backend.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self,session:AsyncSession):
        super().__init__(User,session)

    async def get_by_id(
        self,
        user_id: uuid.UUID
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(
            self,
            email : str
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
    
    async def email_exists(
        self,
        email : str
    )   -> bool:
        return (await self.get_by_email(
            email
        )) is not None
    
    async def get_by_id(
        self,
        user_id: uuid.UUID
    ) -> User | None:

        result = await self.session.execute(
            select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()