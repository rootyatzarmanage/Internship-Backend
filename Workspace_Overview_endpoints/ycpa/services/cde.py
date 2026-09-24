import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.roles import Role
from ycpa.models.user import User
from ycpa.repositories.cde import CdeFileRepository, CdeFolderRepository
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)

DEFAULT_SHARE_ROLE = "BIM Member"


class CdeService(BaseService):
    """CDE operations required by the authentication flow."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = CdeFileRepository(session)
        self.folder_repo = CdeFolderRepository(session)

    async def _get_role(self, role_name: str) -> Role | None:
        return await self.session.scalar(
            select(Role).where(
                Role.name == role_name,
                Role.is_active.is_(True),
                Role.deleted_at.is_(None),
            )
        )

    async def _ensure_project_membership(
        self,
        owner_type: str,
        owner_id: UUID,
        user_id: UUID,
        invited_by: UUID,
        role_name: str = DEFAULT_SHARE_ROLE,
    ) -> None:
        if owner_type == "pim_project":
            from ycpa.models.workspace import PimProjectMember

            member_model = PimProjectMember
        elif owner_type == "aim_project":
            from ycpa.models.workspace import AimProjectMember

            member_model = AimProjectMember
        else:
            return

        existing = await self.session.scalar(
            select(member_model).where(
                member_model.project_id == owner_id,
                member_model.user_id == user_id,
            )
        )
        if existing:
            return

        role = await self._get_role(role_name) or await self._get_role(DEFAULT_SHARE_ROLE)
        self.session.add(
            member_model(
                project_id=owner_id,
                user_id=user_id,
                role_id=role.id if role else None,
                is_share_only=True,
                invited_by=invited_by,
                created_by=invited_by,
            )
        )
        await self.session.flush()

    async def attach_pending_shares_for_user(self, email: str, user_id: UUID) -> int:
        try:
            total = 0
            from ycpa.models.cde import CdePendingFileShare, CdePendingFolderShare

            file_pending_result = await self.session.execute(
                select(CdePendingFileShare).where(
                    CdePendingFileShare.email == email.lower(),
                    CdePendingFileShare.attached_at.is_(None),
                )
            )
            for pending in file_pending_result.scalars().all():
                if not await self.repo.get_share(pending.file_id, user_id):
                    await self.repo.add_share(
                        file_id=pending.file_id,
                        shared_with=user_id,
                        shared_by=pending.shared_by,
                        can_edit=pending.can_edit,
                    )

                file = await self.repo.get_by_id(pending.file_id)
                if file:
                    await self._ensure_project_membership(
                        owner_type=file.owner_type,
                        owner_id=file.owner_id,
                        user_id=user_id,
                        invited_by=pending.shared_by,
                    )

                pending.attached_at = datetime.now(timezone.utc)
                pending.attached_to = user_id
                total += 1

            folder_pending_result = await self.session.execute(
                select(CdePendingFolderShare).where(
                    CdePendingFolderShare.email == email.lower(),
                    CdePendingFolderShare.attached_at.is_(None),
                )
            )
            for pending in folder_pending_result.scalars().all():
                if not await self.folder_repo.get_folder_share(pending.folder_id, user_id):
                    await self.folder_repo.add_folder_share(
                        folder_id=pending.folder_id,
                        shared_with=user_id,
                        shared_by=pending.shared_by,
                        can_edit=pending.can_edit,
                    )

                folder = await self.folder_repo.get_by_id(pending.folder_id)
                if folder:
                    for file in await self.repo.get_all_in_folder_recursive(
                        folder.owner_type, folder.owner_id, pending.folder_id
                    ):
                        if not await self.repo.get_share(file.id, user_id):
                            await self.repo.add_share(
                                file_id=file.id,
                                shared_with=user_id,
                                shared_by=pending.shared_by,
                                can_edit=pending.can_edit,
                            )
                    await self._ensure_project_membership(
                        owner_type=folder.owner_type,
                        owner_id=folder.owner_id,
                        user_id=user_id,
                        invited_by=pending.shared_by,
                    )

                pending.attached_at = datetime.now(timezone.utc)
                pending.attached_to = user_id
                total += 1

            if total:
                await self.session.flush()
            return total
        except Exception:
            await self.session.rollback()
            logger.exception(
                "Failed to attach pending CDE shares for user",
                extra={"user_id": str(user_id), "email": email},
            )
            return 0

    async def seed_sample_file(self, user: User) -> None:
        if await self.repo.has_demo_file(user.id):
            return

        from ycpa.models.cde import CdeFile

        self.session.add(
            CdeFile(
                owner_type="user",
                owner_id=user.id,
                uploaded_by=user.id,
                filename="Sample Building.ifc",
                original_filename="Sample Building.ifc",
                s3_key=f"samples/{user.id}/sample_building.ifc",
                file_size_bytes=0,
                mime_type="application/x-step",
                file_extension="ifc",
                status="published",
                discipline="Architecture",
                description="Sample BIM model — explore the CDE viewer",
                is_demo=True,
                version=1,
                created_by=user.id,
            )
        )
        await self.session.flush()
