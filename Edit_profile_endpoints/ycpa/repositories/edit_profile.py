from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.user import User
from ycpa.models.settings import ProfileSettings
from ycpa.repositories.base import BaseRepository


class EditProfileRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_user(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_profile_settings(
        self,
        user_id: UUID,
    ) -> Optional[ProfileSettings]:

        result = await self.session.execute(
            select(ProfileSettings).where(
                ProfileSettings.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        user: User,
        profile: ProfileSettings,
        data: dict,
    ) -> tuple[User, ProfileSettings]:

        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        if "first_name" in data or "last_name" in data:
            current_parts = user.full_name.split(maxsplit=1)

            existing_first = current_parts[0] if current_parts else ""
            existing_last = current_parts[1] if len(current_parts) > 1 else ""

            first_name = data.get("first_name", existing_first)
            last_name = data.get("last_name", existing_last)

            user.full_name = f"{first_name} {last_name}".strip()
            profile.name = user.full_name

        if "email" in data:
            user.email = data["email"].lower()
            profile.email_id = user.email

        if "country_code" in data or "phone" in data:
            country_code = data.get("country_code", "+91")
            phone = data.get("phone", "")

            full_phone = f"{country_code}{phone}".replace(" ", "")

            user.phone = full_phone
            profile.contact_number = full_phone

        for field in ("country", "state", "district", "pincode"):
            if field in data:
                setattr(profile, field, data[field] or "")

        user.updated_at = datetime.now(timezone.utc)

        await self.session.flush()

        return user, profile