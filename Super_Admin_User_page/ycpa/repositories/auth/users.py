import logging
from typing import Optional
from uuid import UUID
 
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
 
from ycpa.models.storage_usage import StorageUsage
from ycpa.models.subscription import AimSubscription, PimSubscription
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository
 
logger = logging.getLogger(__name__)
 
 
class UserRepository(BaseRepository[User]):
 
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
 
 
    async def get_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .where(User.cognito_sub == cognito_sub)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
 
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(
                func.lower(User.email) == email.lower(),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
 
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
 
 
    async def search(
        self,
        q: str,
        exclude_id: UUID,
        limit: int = 10,
    ) -> list[User]:
 
        term = f"%{q.lower().strip()}%"
        result = await self.session.execute(
            select(User)
            .where(
                User.deleted_at.is_(None),
                User.is_active.is_(True),
                User.id != exclude_id,
                or_(
                    func.lower(User.email).like(term),
                    func.lower(User.full_name).like(term),
                ),
            )
            .order_by(User.full_name)
            .limit(limit)
        )
        return list(result.scalars().all())
 
 
    async def get_storage_usage(self, user_id: UUID) -> StorageUsage | None:
        result = await self.session.execute(
            select(StorageUsage).where(StorageUsage.user_id == user_id)
        )
        return result.scalar_one_or_none()
 
    async def get_pim_subscription(self, user_id: UUID) -> PimSubscription | None:
        result = await self.session.execute(
            select(PimSubscription).where(PimSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()
 
    async def get_aim_subscription(self, user_id: UUID) -> AimSubscription | None:
        result = await self.session.execute(
            select(AimSubscription).where(AimSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()