from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.exceptions import NotFoundException
from ycpa.models.settings import ProfileSettings
from ycpa.repositories.edit_profile import EditProfileRepository


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024


class EditProfileService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EditProfileRepository(session)

        settings = get_settings()

        self.storage_dir = Path(
            settings.LOCAL_STORAGE_PATH
        ).resolve()

    async def edit_profile(
        self,
        user_id: UUID,
        data: dict,
        image: UploadFile | None = None,
    ) -> dict:

        user = await self.repository.get_user(user_id)

        if not user:
            raise NotFoundException(
                message="User not found",
                resource="user",
            )

        profile = await self.repository.get_profile_settings(
            user_id
        )

        if profile is None:
            profile = ProfileSettings(
                user_id=user.id,
                name=user.full_name,
                email_id=user.email,
                profile_image=None,
                contact_number=user.phone or "",
                contact_address="",
                country="",
                state="",
                district="",
                pincode="",
            )

            self.session.add(profile)

        new_image_path = None

        try:
            first_name = data.get("first_name")
            last_name = data.get("last_name")

            if first_name is not None or last_name is not None:

                existing_parts = (user.full_name or "").split(
                    maxsplit=1
                )

                current_first = (
                    existing_parts[0] if existing_parts else ""
                )

                current_last = (
                    existing_parts[1]
                    if len(existing_parts) > 1
                    else ""
                )

                first_name = (
                    first_name
                    if first_name is not None
                    else current_first
                )

                last_name = (
                    last_name
                    if last_name is not None
                    else current_last
                )

                user.full_name = " ".join(
                    part for part in [first_name, last_name] if part
                )

                profile.name = user.full_name
                
            country_code = data.get("country_code")
            phone = data.get("phone")

            if phone is not None or country_code is not None:

                existing_phone = user.phone or ""

                if phone is None:
                    phone = existing_phone

                if country_code is None:
                    country_code = "+91"

                user.phone = f"{country_code}{phone}"

                profile.contact_number = user.phone

            for field in [
                "country",
                "state",
                "district",
                "pincode",
            ]:
                if field in data:
                    setattr(profile, field, data[field] or "")

            if image and image.filename:

                if image.content_type not in ALLOWED_IMAGE_TYPES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Only JPG, PNG and WEBP images are allowed",
                    )

                content = await image.read()

                if not content:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Uploaded image is empty",
                    )

                if len(content) > MAX_IMAGE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Image must be smaller than 5 MB",
                    )

                extension = ALLOWED_IMAGE_TYPES[
                    image.content_type
                ]

                user_profile_image_dir = (
                    self.storage_dir
                    / str(user_id)
                    / "profile_images"
                )

                user_profile_image_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                filename = f"{uuid4().hex}{extension}"
                new_image_path = user_profile_image_dir / filename
                new_image_path.write_bytes(content)
                profile.profile_image = str(
                    Path(str(user_id)) / "profile_images" / filename
                )

            if "delete" in data:
                delete_value = data["delete"]
                if delete_value == 1:

                    if user.deleted_at is None:
                        user.deleted_at = datetime.now(timezone.utc)
                        user.deleted_by = user.id

                    user.is_active = False

                elif delete_value == 0:

                    if user.deleted_at is not None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Deleted account cannot be reactivated through profile update",
                        )

            await self.session.commit()

            await self.session.refresh(user)
            await self.session.refresh(profile)

            name_parts = (user.full_name or "").split(
                maxsplit=1
            )

            return {
                "user_id": user.id,
                "first_name": (
                    name_parts[0] if name_parts else ""
                ),
                "last_name": (
                    name_parts[1]
                    if len(name_parts) > 1
                    else ""
                ),
                "email": user.email,
                "country_code": country_code or "+91",
                "phone": phone if phone is not None else user.phone,
                "country": profile.country,
                "state": profile.state,
                "district": profile.district,
                "pincode": profile.pincode,
                "delete": 1 if user.deleted_at is not None else 0,
                "deleted_at": user.deleted_at,
                "updated_at": user.updated_at,
            }

        except Exception:
            await self.session.rollback()

            if new_image_path and new_image_path.exists():
                new_image_path.unlink()

            raise

    async def get_profile_image_path(
        self,
        user_id: UUID,
    ) -> Path:

        profile = await self.repository.get_profile_settings(
            user_id
        )

        if not profile or not profile.profile_image:
            raise NotFoundException(
                message="Profile image not found",
                resource="profile image",
            )

        image_path = (
            self.storage_dir / profile.profile_image
        ).resolve()

        if not image_path.is_relative_to(self.storage_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image path",
            )

        if not image_path.is_file():
            raise NotFoundException(
                message="Profile image file not found",
                resource="profile image",
            )

        return image_path

    async def get_profile(self, user_id: UUID) -> dict:

        user = await self.repository.get_user(user_id)
        if not user:
            raise NotFoundException(
                message="User not found",
                resource="user",
            )

        profile = await self.repository.get_profile_settings(user_id)
        name_parts = (user.full_name or "").split(maxsplit=1)

        return {
            "user_id": user.id,
            "first_name": name_parts[0] if name_parts else "",
            "last_name": name_parts[1] if len(name_parts) > 1 else "",
            "email": user.email,
            "country_code": "+91",
            "phone": user.phone,
            "country": profile.country if profile else "",
            "state": profile.state if profile else "",
            "district": profile.district if profile else "",
            "pincode": profile.pincode if profile else "",
            "updated_at": user.updated_at,
            "delete": 1 if user.deleted_at is not None else 0,
            "deleted_at": user.deleted_at,
        }   