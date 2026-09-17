import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.file import File
from backend.repositories.base import BaseRepository

class FileRepository(BaseRepository[File]):
        def __init__(self, session:AsyncSession):
                super().__init__(File, session)
        async def get_by_id(
                self,
                file_id : uuid.UUID,
                user_id : uuid.UUID
        )-> File | None:
                result = await self.session.execute(
                        select(File).where(
                                File.id == file_id,
                                File.user_id == user_id,
                                File.deleted_at.is_(None)
                        )
                )
                return result.scalar_one_or_none()

        async def get_all_by_user(
                self,
                user_id : uuid.UUID                
        )-> list[File] | None:
                result = await self.session.execute(
                        select(File).where(
                               File.user_id == user_id,
                               File.deleted_at.is_(None)
                        )
                )
                return list(result.scalars().all())
        