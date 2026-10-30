import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.cde import (
    CdeFile,
    CdeFileShare,
    CdeFolder,
    CdeFolderShare,
    CdeGroup,
    CdePendingFileShare,
    CdePendingFolderShare,
)
from ycpa.models.roles import Role
from ycpa.models.user import User
from ycpa.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


async def _get_accepted_folder_share(session, folder_id: UUID, user_id: UUID):

    current_id = folder_id
    visited: set[UUID] = set()

    for _ in range(20):
        if current_id is None or current_id in visited:
            break
        visited.add(current_id)

        share = await session.scalar(
            select(CdeFolderShare).where(
                CdeFolderShare.folder_id   == current_id,
                CdeFolderShare.shared_with == user_id,
                CdeFolderShare.status      == "accepted",
                CdeFolderShare.deleted_at.is_(None),
            )
        )
        if share:
            return share

        folder = await session.scalar(
            select(CdeFolder).where(
                CdeFolder.id         == current_id,
                CdeFolder.deleted_at.is_(None),
            )
        )
        if not folder or folder.parent_id is None:
            break
        current_id = folder.parent_id

    return None



class CdeFileRepository(BaseRepository[CdeFile]):

    def __init__(self, session: AsyncSession):
        super().__init__(CdeFile, session)

    async def get_by_id(self, file_id: UUID, include_deleted: bool = False) -> CdeFile | None:
        query = select(CdeFile).where(CdeFile.id == file_id)
        if not include_deleted:
            query = query.where(CdeFile.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_owner(
        self,
        owner_type: str,
        owner_id:   UUID,
        folder_id:  UUID | None,
        status:     str | None = None,
    ) -> list[CdeFile]:
        query = select(CdeFile).where(
            CdeFile.owner_type       == owner_type,
            CdeFile.owner_id         == owner_id,
            CdeFile.deleted_at.is_(None),
            or_(CdeFile.parent_file_id.is_(None), CdeFile.file_extension != "frag"),
        )
        if folder_id is None:
            query = query.where(CdeFile.folder_id.is_(None))
        else:
            query = query.where(CdeFile.folder_id == folder_id)

        if status:
            query = query.where(CdeFile.status == status)

        query = query.order_by(CdeFile.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_owner_and_uploader(
        self,
        owner_type: str,
        owner_id:   UUID,
        folder_id:  UUID | None,
        user_id:    UUID,
    ) -> list[CdeFile]:
        query = select(CdeFile).where(
            CdeFile.owner_type       == owner_type,
            CdeFile.owner_id         == owner_id,
            CdeFile.deleted_at.is_(None),
            or_(CdeFile.parent_file_id.is_(None), CdeFile.file_extension != "frag"),
            CdeFile.uploaded_by      == user_id,
        )
        if folder_id is None:
            query = query.where(CdeFile.folder_id.is_(None))
        else:
            query = query.where(CdeFile.folder_id == folder_id)

        query = query.order_by(CdeFile.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_by_owner(
        self,
        owner_type: str,
        owner_id:   UUID,
        status:     str | None = None,
    ) -> list[CdeFile]:
        query = select(CdeFile).where(
            CdeFile.owner_type       == owner_type,
            CdeFile.owner_id         == owner_id,
            CdeFile.deleted_at.is_(None),
            or_(CdeFile.parent_file_id.is_(None), CdeFile.file_extension != "frag"),
        )
        if status:
            query = query.where(CdeFile.status == status)
        query = query.order_by(CdeFile.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_in_folder_recursive(
        self, owner_type: str, owner_id: UUID, folder_id: UUID
    ) -> list[CdeFile]:
        all_files: list[CdeFile] = []
        folder_queue: list[UUID] = [folder_id]
        visited: set[UUID] = set()

        while folder_queue:
            current_folder_id = folder_queue.pop(0)
            if current_folder_id in visited:
                continue
            visited.add(current_folder_id)

            files = await self.get_by_owner(owner_type, owner_id, current_folder_id)
            all_files.extend(files)

            result = await self.session.execute(
                select(CdeFolder).where(
                    CdeFolder.parent_id  == current_folder_id,
                    CdeFolder.owner_type == owner_type,
                    CdeFolder.owner_id   == owner_id,
                    CdeFolder.deleted_at.is_(None),
                )
            )
            sub_folders = list(result.scalars().all())
            folder_queue.extend(sf.id for sf in sub_folders)

        return all_files

    async def move_to_folder(
        self, file_id: UUID, folder_id: UUID | None, updated_by: UUID
    ) -> None:
        await self.session.execute(
            update(CdeFile)
            .where(CdeFile.id == file_id)
            .values(
                folder_id  = folder_id,
                updated_by = updated_by,
                updated_at = datetime.now(timezone.utc),
            )
        )
        await self.session.flush()

    async def get_all_visible(
        self,
        user_id: UUID,
        owner_type: str | None = None,
        owner_id: UUID | None = None,
        file_extension: str | None = None,
    ) -> list[CdeFile]:
        from ycpa.models.workspace import (
            AimProject, AimProjectMember, AimWorkspace, AimWorkspaceMember,
            PimProject, PimProjectMember, PimWorkspace, PimWorkspaceMember,
        )

        pim_member_subq = (
            select(PimProjectMember.project_id).where(
                PimProjectMember.user_id == user_id,
            )
        )
        aim_member_subq = (
            select(AimProjectMember.project_id).where(
                AimProjectMember.user_id == user_id,
            )
        )

        pim_ws_subq = select(PimWorkspace.id).where(
            or_(
                PimWorkspace.owner_id == user_id,
                PimWorkspace.id.in_(
                    select(PimWorkspaceMember.workspace_id).where(
                        PimWorkspaceMember.user_id == user_id,
                        PimWorkspaceMember.role.in_(["owner", "admin"]),
                    )
                ),
            ),
            PimWorkspace.deleted_at.is_(None),
        )
        pim_admin_proj_subq = select(PimProject.id).where(
            PimProject.workspace_id.in_(pim_ws_subq),
            PimProject.deleted_at.is_(None),
        )

        aim_ws_subq = select(AimWorkspace.id).where(
            or_(
                AimWorkspace.owner_id == user_id,
                AimWorkspace.id.in_(
                    select(AimWorkspaceMember.workspace_id).where(
                        AimWorkspaceMember.user_id == user_id,
                        AimWorkspaceMember.role.in_(["owner", "admin"]),
                    )
                ),
            ),
            AimWorkspace.deleted_at.is_(None),
        )
        aim_admin_proj_subq = select(AimProject.id).where(
            AimProject.workspace_id.in_(aim_ws_subq),
            AimProject.deleted_at.is_(None),
        )

        stmt = (
            select(CdeFile).where(
                CdeFile.deleted_at.is_(None),
                or_(CdeFile.parent_file_id.is_(None), CdeFile.file_extension != "frag"),
                or_(
                    CdeFile.uploaded_by == user_id,
                    CdeFile.id.in_(
                        select(CdeFileShare.file_id).where(
                            CdeFileShare.shared_with == user_id,
                            CdeFileShare.status      == "accepted",
                            CdeFileShare.deleted_at.is_(None),
                        )
                    ),
                    and_(
                        CdeFile.owner_type == "pim_project",
                        or_(
                            CdeFile.owner_id.in_(pim_member_subq),
                            CdeFile.owner_id.in_(pim_admin_proj_subq),
                        ),
                    ),
                    and_(
                        CdeFile.owner_type == "aim_project",
                        or_(
                            CdeFile.owner_id.in_(aim_member_subq),
                            CdeFile.owner_id.in_(aim_admin_proj_subq),
                        ),
                    ),
                ),
            ).order_by(CdeFile.created_at.desc())
        )
        if owner_type:
            stmt = stmt.where(CdeFile.owner_type == owner_type)
        if owner_id:
            stmt = stmt.where(CdeFile.owner_id == owner_id)
        if file_extension:
            stmt = stmt.where(CdeFile.file_extension == file_extension)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_member_role(
        self, owner_type: str, owner_id: UUID, user_id: UUID
    ) -> str | None:
        """Return the role name for a project member, or None if not a member."""
        from ycpa.models.workspace import AimProjectMember, PimProjectMember

        if owner_type == "pim_project":
            member_model = PimProjectMember
        elif owner_type == "aim_project":
            member_model = AimProjectMember
        else:
            return None

        member = await self.session.scalar(
            select(member_model).where(
                member_model.project_id == owner_id,
                member_model.user_id    == user_id,
            )
        )
        if not member or not member.role_id:
            return None

        role = await self.session.scalar(
            select(Role).where(Role.id == member.role_id)
        )
        return role.name if role else None

    async def get_frag_child(self, parent_id: UUID) -> CdeFile | None:
        result = await self.session.execute(
            select(CdeFile).where(
                CdeFile.parent_file_id == parent_id,
                CdeFile.file_extension == "frag",
                CdeFile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def has_demo_file(self, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(func.count()).select_from(CdeFile).where(
                CdeFile.uploaded_by == user_id,
                CdeFile.is_demo.is_(True),
                CdeFile.deleted_at.is_(None),
            )
        )
        return (result.scalar() or 0) > 0

    async def get_frag_children(self, parent_ids: list[UUID]) -> dict[UUID, CdeFile]:
        if not parent_ids:
            return {}
        result = await self.session.execute(
            select(CdeFile).where(
                CdeFile.parent_file_id.in_(parent_ids),
                CdeFile.file_extension == "frag",
                CdeFile.deleted_at.is_(None),
            )
        )
        return {f.parent_file_id: f for f in result.scalars().all()}

    async def count_shares_batch(self, file_ids: list[UUID]) -> dict[UUID, int]:
        if not file_ids:
            return {}
        result = await self.session.execute(
            select(CdeFileShare.file_id, func.count())
            .where(
                CdeFileShare.file_id.in_(file_ids),
                CdeFileShare.status == "accepted",
                CdeFileShare.deleted_at.is_(None),
            )
            .group_by(CdeFileShare.file_id)
        )
        counts = dict(result.all())
        return {fid: counts.get(fid, 0) for fid in file_ids}

    async def can_edit_batch(self, files: list[CdeFile], user_id: UUID) -> dict[UUID, bool]:
        if not files:
            return {}

        file_ids = [f.id for f in files]
        result = {f.id: f.uploaded_by == user_id for f in files}

        remaining = [fid for fid in file_ids if not result[fid]]
        if not remaining:
            return result

        share_rows = await self.session.execute(
            select(CdeFileShare.file_id).where(
                CdeFileShare.file_id.in_(remaining),
                CdeFileShare.shared_with == user_id,
                CdeFileShare.can_edit.is_(True),
                CdeFileShare.status == "accepted",
                CdeFileShare.deleted_at.is_(None),
            )
        )
        for (fid,) in share_rows.all():
            result[fid] = True

        remaining = [fid for fid in remaining if not result[fid]]
        if not remaining:
            return result

        files_by_id = {f.id: f for f in files}
        for fid in remaining:
            f = files_by_id[fid]
            if f.folder_id:
                folder_share = await _get_accepted_folder_share(self.session, f.folder_id, user_id)
                if folder_share and folder_share.can_edit:
                    result[fid] = True

        return result

    async def can_delete_batch(self, files: list[CdeFile], user_id: UUID) -> dict[UUID, bool]:
        if not files:
            return {}

        edit_map = await self.can_edit_batch(files, user_id)

        result: dict[UUID, bool] = {}
        for f in files:
            if not edit_map.get(f.id, False):
                result[f.id] = False
            elif f.owner_type in ("pim_project", "aim_project"):
                result[f.id] = False
            else:
                result[f.id] = True

        project_files = [f for f in files if f.owner_type in ("pim_project", "aim_project")]
        if project_files:
            project_ids = {(f.owner_type, f.owner_id) for f in project_files}
            role_cache: dict[tuple[str, UUID], str | None] = {}
            for owner_type, owner_id in project_ids:
                role_cache[(owner_type, owner_id)] = await self.get_member_role(
                    owner_type, owner_id, user_id
                )
            for f in project_files:
                role_name = role_cache.get((f.owner_type, f.owner_id))
                if role_name in ("Admin", "BIM Manager", "Owner"):
                    result[f.id] = True

        return result

    async def can_view(self, file_id: UUID, user_id: UUID) -> bool:
        file = await self.session.scalar(
            select(CdeFile).where(
                CdeFile.id         == file_id,
                CdeFile.deleted_at.is_(None),
            )
        )
        if not file:
            return False
        if file.uploaded_by == user_id:
            return True
        if file.owner_type in ("pim_project", "aim_project"):
            from ycpa.services.rbac import RBACService
            ws_type = "pim" if file.owner_type == "pim_project" else "aim"
            ws_role = await RBACService.get_workspace_role_for_project(
                self.session, user_id, file.owner_id, ws_type
            )
            if ws_role in ("owner", "admin"):
                return True

            from ycpa.models.workspace import AimProjectMember, PimProjectMember
            member_model = (
                PimProjectMember if file.owner_type == "pim_project" else AimProjectMember
            )
            member = await self.session.scalar(
                select(member_model).where(
                    member_model.project_id == file.owner_id,
                    member_model.user_id == user_id,
                )
            )
            if member:
                return True

        file_share = await self.session.scalar(
            select(CdeFileShare).where(
                CdeFileShare.file_id     == file_id,
                CdeFileShare.shared_with == user_id,
                CdeFileShare.status      == "accepted",
                CdeFileShare.deleted_at.is_(None),
            )
        )
        if file_share:
            return True

        if file.folder_id:
            folder_share = await _get_accepted_folder_share(
                self.session, file.folder_id, user_id
            )
            if folder_share:
                return True

        return False

    async def can_edit(self, file_id: UUID, user_id: UUID) -> bool:
        file = await self.session.scalar(
            select(CdeFile).where(
                CdeFile.id         == file_id,
                CdeFile.deleted_at.is_(None),
            )
        )
        if not file:
            return False
        if file.uploaded_by == user_id:
            return True

        file_share = await self.session.scalar(
            select(CdeFileShare).where(
                CdeFileShare.file_id     == file_id,
                CdeFileShare.shared_with == user_id,
                CdeFileShare.can_edit.is_(True),
                CdeFileShare.status      == "accepted",
                CdeFileShare.deleted_at.is_(None),
            )
        )
        if file_share:
            return True

        if file.folder_id:
            folder_share = await _get_accepted_folder_share(
                self.session, file.folder_id, user_id
            )
            if folder_share and folder_share.can_edit:
                return True

        return False

    async def count_shares(self, file_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(CdeFileShare).where(
                CdeFileShare.file_id     == file_id,
                CdeFileShare.status      == "accepted",
                CdeFileShare.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def get_share(self, file_id: UUID, user_id: UUID) -> Optional[CdeFileShare]:
        result = await self.session.execute(
            select(CdeFileShare).where(
                CdeFileShare.file_id     == file_id,
                CdeFileShare.shared_with == user_id,
                CdeFileShare.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_shares_with_users(
        self, file_id: UUID
    ) -> list[tuple[CdeFileShare, User]]:
        result = await self.session.execute(
            select(CdeFileShare, User)
            .join(User, User.id == CdeFileShare.shared_with)
            .where(
                CdeFileShare.file_id     == file_id,
                CdeFileShare.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(CdeFileShare.shared_at)
        )
        return list(result.all())

    async def add_share(
        self,
        file_id:     UUID,
        shared_with: UUID,
        shared_by:   UUID,
        can_edit:    bool = False,
    ) -> CdeFileShare:
        share = CdeFileShare(
            file_id     = file_id,
            shared_with = shared_with,
            shared_by   = shared_by,
            can_edit    = can_edit,
            token       = secrets.token_urlsafe(32),
            status      = "accepted",
            expires_at  = datetime.now(timezone.utc) + timedelta(days=365),
            created_by  = shared_by,
        )
        self.session.add(share)
        await self.session.flush()
        return share

    async def get_pending_share(
        self, file_id: UUID, email: str
    ) -> Optional[CdePendingFileShare]:
        result = await self.session.execute(
            select(CdePendingFileShare).where(
                CdePendingFileShare.file_id      == file_id,
                CdePendingFileShare.email        == email,
                CdePendingFileShare.attached_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def add_pending_share(
        self,
        file_id:   UUID,
        email:     str,
        shared_by: UUID,
        can_edit:  bool,
    ) -> CdePendingFileShare:
        pending = CdePendingFileShare(
            file_id   = file_id,
            email     = email,
            shared_by = shared_by,
            can_edit  = can_edit,
            shared_at = datetime.now(timezone.utc),
        )
        self.session.add(pending)
        await self.session.flush()
        return pending

    async def get_pending_shares_with_email(
        self, file_id: UUID
    ) -> list[CdePendingFileShare]:
        result = await self.session.execute(
            select(CdePendingFileShare).where(
                CdePendingFileShare.file_id      == file_id,
                CdePendingFileShare.attached_at.is_(None),
            ).order_by(CdePendingFileShare.shared_at)
        )
        return list(result.scalars().all())

    async def attach_pending_shares(self, email: str, user_id: UUID) -> int:
        result = await self.session.execute(
            select(CdePendingFileShare).where(
                CdePendingFileShare.email        == email,
                CdePendingFileShare.attached_at.is_(None),
            )
        )
        pending_shares = list(result.scalars().all())
        count = 0

        for ps in pending_shares:
            existing = await self.get_share(ps.file_id, user_id)
            if not existing:
                await self.add_share(
                    file_id     = ps.file_id,
                    shared_with = user_id,
                    shared_by   = ps.shared_by,
                    can_edit    = ps.can_edit,
                )
            ps.attached_at = datetime.now(timezone.utc)
            ps.attached_to = user_id
            count += 1

        if count:
            await self.session.flush()
        return count

    # ── NEW: discipline-filtered file query ───────────────────────────────────

    async def get_by_owner_discipline_filtered(
        self,
        owner_type:    str,
        owner_id:      UUID,
        folder_id:     Optional[UUID],
        discipline_id: Optional[UUID],
        user_id:       UUID,
    ) -> list[CdeFile]:
        """
        Returns files in a folder with discipline-based WIP filtering.

        Rules:
          discipline_id is None → no restriction, return all files
          discipline_id is UUID →
            - WIP files:                  only show if file.discipline matches
                                          OR file.discipline is NULL
            - shared/published/archived:  always show
            - own uploads:                always show (uploader sees their own WIP)
        """
        query = select(CdeFile).where(
            CdeFile.owner_type       == owner_type,
            CdeFile.owner_id         == owner_id,
            CdeFile.deleted_at.is_(None),
            or_(CdeFile.parent_file_id.is_(None), CdeFile.file_extension != "frag"),
        )

        if folder_id is None:
            query = query.where(CdeFile.folder_id.is_(None))
        else:
            query = query.where(CdeFile.folder_id == folder_id)

        if discipline_id is not None:
            # Resolve discipline name — CdeFile.discipline is Text not UUID
            from ycpa.models.workspace import PimScopeDiscipline
            discipline_obj = await self.session.scalar(
                select(PimScopeDiscipline).where(
                    PimScopeDiscipline.id         == discipline_id,
                    PimScopeDiscipline.deleted_at.is_(None),
                )
            )
            discipline_name = discipline_obj.name if discipline_obj else None

            if discipline_name:
                query = query.where(
                    or_(
                        CdeFile.status      != "wip",               # shared/published/archived → always show
                        CdeFile.uploaded_by == user_id,             # own files → always show
                        CdeFile.discipline.is_(None),               # WIP no discipline tag → show to all
                        CdeFile.discipline  == discipline_name,     # WIP matching discipline → show
                    )
                )

        query = query.order_by(CdeFile.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())


# ── CdeFolderRepository ───────────────────────────────────────────────────────

class CdeFolderRepository(BaseRepository[CdeFolder]):

    def __init__(self, session: AsyncSession):
        super().__init__(CdeFolder, session)

    async def get_by_id(self, folder_id: UUID) -> Optional[CdeFolder]:
        result = await self.session.execute(
            select(CdeFolder).where(
                CdeFolder.id         == folder_id,
                CdeFolder.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_children(
        self,
        owner_type: str,
        owner_id:   UUID,
        parent_id:  Optional[UUID],
    ) -> list[CdeFolder]:
        query = select(CdeFolder).where(
            CdeFolder.owner_type == owner_type,
            CdeFolder.owner_id   == owner_id,
            CdeFolder.deleted_at.is_(None),
        )
        if parent_id is None:
            query = query.where(CdeFolder.parent_id.is_(None))
        else:
            query = query.where(CdeFolder.parent_id == parent_id)

        query = query.order_by(CdeFolder.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_ancestors(self, folder_id: UUID) -> list[CdeFolder]:
        ancestors: list[CdeFolder] = []
        current_id: Optional[UUID] = folder_id

        for _ in range(20):
            if current_id is None:
                break
            folder = await self.get_by_id(current_id)
            if not folder:
                break
            ancestors.insert(0, folder)
            current_id = folder.parent_id

        # Remove the target folder itself (it's the current folder, not an ancestor)
        if ancestors and ancestors[-1].id == folder_id:
            ancestors.pop()

        return ancestors

    async def name_exists_in_parent(
        self,
        owner_type:  str,
        owner_id:    UUID,
        name:        str,
        parent_id:   Optional[UUID],
        exclude_id:  Optional[UUID] = None,
    ) -> bool:
        query = select(func.count()).select_from(CdeFolder).where(
            CdeFolder.owner_type == owner_type,
            CdeFolder.owner_id   == owner_id,
            CdeFolder.name       == name,
            CdeFolder.deleted_at.is_(None),
        )
        if parent_id is None:
            query = query.where(CdeFolder.parent_id.is_(None))
        else:
            query = query.where(CdeFolder.parent_id == parent_id)
        if exclude_id:
            query = query.where(CdeFolder.id != exclude_id)

        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

    async def count_children(self, folder_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(CdeFolder).where(
                CdeFolder.parent_id  == folder_id,
                CdeFolder.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def rename(
        self, folder_id: UUID, name: str, updated_by: UUID
    ) -> Optional[CdeFolder]:
        await self.session.execute(
            update(CdeFolder)
            .where(CdeFolder.id == folder_id)
            .values(
                name       = name,
                updated_by = updated_by,
                updated_at = datetime.now(timezone.utc),
            )
        )
        await self.session.flush()
        return await self.get_by_id(folder_id)

    async def soft_delete(self, folder_id: UUID, deleted_by: UUID) -> None:
        await self.session.execute(
            update(CdeFolder)
            .where(CdeFolder.id == folder_id)
            .values(
                deleted_at = datetime.now(timezone.utc),
                deleted_by = deleted_by,
            )
        )
        await self.session.flush()

    async def get_folder_share(
        self, folder_id: UUID, user_id: UUID
    ) -> Optional[CdeFolderShare]:
        result = await self.session.execute(
            select(CdeFolderShare).where(
                CdeFolderShare.folder_id   == folder_id,
                CdeFolderShare.shared_with == user_id,
                CdeFolderShare.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_folder_shares_with_users(
        self, folder_id: UUID
    ) -> list[tuple[CdeFolderShare, User]]:
        result = await self.session.execute(
            select(CdeFolderShare, User)
            .join(User, User.id == CdeFolderShare.shared_with)
            .where(
                CdeFolderShare.folder_id   == folder_id,
                CdeFolderShare.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(CdeFolderShare.shared_at)
        )
        return list(result.all())

    async def add_folder_share(
        self,
        folder_id:   UUID,
        shared_with: UUID,
        shared_by:   UUID,
        can_edit:    bool = False,
    ) -> CdeFolderShare:
        share = CdeFolderShare(
            folder_id   = folder_id,
            shared_with = shared_with,
            shared_by   = shared_by,
            can_edit    = can_edit,
            token       = secrets.token_urlsafe(32),
            status      = "accepted",
            expires_at  = datetime.now(timezone.utc) + timedelta(days=365),
            created_by  = shared_by,
        )
        self.session.add(share)
        await self.session.flush()
        return share

    async def get_pending_folder_share(
        self, folder_id: UUID, email: str
    ) -> Optional[CdePendingFolderShare]:
        result = await self.session.execute(
            select(CdePendingFolderShare).where(
                CdePendingFolderShare.folder_id    == folder_id,
                CdePendingFolderShare.email        == email,
                CdePendingFolderShare.attached_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_folder_shares(
        self, folder_id: UUID
    ) -> list[CdePendingFolderShare]:
        result = await self.session.execute(
            select(CdePendingFolderShare).where(
                CdePendingFolderShare.folder_id    == folder_id,
                CdePendingFolderShare.attached_at.is_(None),
            ).order_by(CdePendingFolderShare.shared_at)
        )
        return list(result.scalars().all())

    async def add_pending_folder_share(
        self,
        folder_id: UUID,
        email:     str,
        shared_by: UUID,
        can_edit:  bool,
    ) -> CdePendingFolderShare:
        pending = CdePendingFolderShare(
            folder_id = folder_id,
            email     = email,
            shared_by = shared_by,
            can_edit  = can_edit,
            shared_at = datetime.now(timezone.utc),
        )
        self.session.add(pending)
        await self.session.flush()
        return pending

    async def attach_pending_folder_shares(self, email: str, user_id: UUID) -> int:
        result = await self.session.execute(
            select(CdePendingFolderShare).where(
                CdePendingFolderShare.email        == email,
                CdePendingFolderShare.attached_at.is_(None),
            )
        )
        pending_list = list(result.scalars().all())
        count = 0

        for pf in pending_list:
            existing = await self.get_folder_share(pf.folder_id, user_id)
            if not existing:
                await self.add_folder_share(
                    folder_id   = pf.folder_id,
                    shared_with = user_id,
                    shared_by   = pf.shared_by,
                    can_edit    = pf.can_edit,
                )
            pf.attached_at = datetime.now(timezone.utc)
            pf.attached_to = user_id
            count += 1

        if count:
            await self.session.flush()
        return count

    async def get_accessible_folder_ids_for_user(
        self,
        owner_type:     str,
        owner_id:       UUID,
        user_id:        UUID,
        workspace_type: str,
    ) -> set[UUID] | None:
        """
        Returns:
          None      → user is a real project member → show ALL folders (no restriction)
          set[UUID] → share-only user → show ONLY these folder IDs (shared + ancestors)
          set()     → no access at all
        """
        if workspace_type == "pim":
            from ycpa.models.workspace import PimProjectMember
            member_model = PimProjectMember
        else:
            from ycpa.models.workspace import AimProjectMember
            member_model = AimProjectMember

        member = await self.session.scalar(
            select(member_model).where(
                member_model.project_id == owner_id,
                member_model.user_id    == user_id,
            )
        )
        if member and not getattr(member, "is_share_only", False):
            return None  # Full project member → unrestricted

        shared_rows = await self.session.scalars(
            select(CdeFolderShare).where(
                CdeFolderShare.shared_with == user_id,
                CdeFolderShare.status      == "accepted",
                CdeFolderShare.deleted_at.is_(None),
            )
        )
        shared_folder_ids: set[UUID] = {row.folder_id for row in shared_rows}

        if not shared_folder_ids:
            return set()

        project_folder_ids: set[UUID] = set()
        for fid in shared_folder_ids:
            folder = await self.get_by_id(fid)
            if folder and folder.owner_type == owner_type and folder.owner_id == owner_id:
                project_folder_ids.add(fid)

        if not project_folder_ids:
            return set()

        all_visible: set[UUID] = set(project_folder_ids)

        for folder_id in project_folder_ids:
            current_id: UUID | None = folder_id
            visited: set[UUID] = set()
            for _ in range(20):
                if current_id is None or current_id in visited:
                    break
                visited.add(current_id)
                folder = await self.get_by_id(current_id)
                if not folder or folder.parent_id is None:
                    break
                all_visible.add(folder.parent_id)
                current_id = folder.parent_id

        return all_visible

    async def get_children_for_user(
        self,
        owner_type:     str,
        owner_id:       UUID,
        parent_id:      Optional[UUID],
        user_id:        UUID,
        workspace_type: str,
    ) -> list[CdeFolder]:
        """
        Like get_children() but filters by what the user is allowed to see.
        Full project members see everything.
        Share-only users see only shared folders + their ancestors.
        """
        accessible = await self.get_accessible_folder_ids_for_user(
            owner_type, owner_id, user_id, workspace_type
        )

        query = select(CdeFolder).where(
            CdeFolder.owner_type == owner_type,
            CdeFolder.owner_id   == owner_id,
            CdeFolder.deleted_at.is_(None),
        )
        if parent_id is None:
            query = query.where(CdeFolder.parent_id.is_(None))
        else:
            query = query.where(CdeFolder.parent_id == parent_id)

        if accessible is not None:
            if not accessible:
                return []
            query = query.where(CdeFolder.id.in_(accessible))

        query = query.order_by(CdeFolder.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ── NEW: discipline-filtered folder query ─────────────────────────────────

    async def get_children_discipline_filtered(
        self,
        owner_type:    str,
        owner_id:      UUID,
        parent_id:     Optional[UUID],
        discipline_id: Optional[UUID],
    ) -> list[CdeFolder]:
        """
        Returns child folders with discipline-based WIP filtering.

        Rules:
          discipline_id is None → no restriction, return all folders
          discipline_id is UUID →
            - WIP folders:               only show if folder.discipline_id matches
                                         OR folder.discipline_id is NULL
            - shared/published/archived: always show

        Why show discipline_id=NULL WIP folders?
          Root-level and cross-discipline folders have no tag — visible to everyone.
        """
        query = select(CdeFolder).where(
            CdeFolder.owner_type == owner_type,
            CdeFolder.owner_id   == owner_id,
            CdeFolder.deleted_at.is_(None),
        )

        if parent_id is None:
            query = query.where(CdeFolder.parent_id.is_(None))
        else:
            query = query.where(CdeFolder.parent_id == parent_id)

        if discipline_id is not None:
            query = query.where(
                or_(
                    CdeFolder.status        != "wip",            # shared/published/archived → always show
                    CdeFolder.discipline_id.is_(None),           # WIP no discipline tag → show to all
                     CdeFolder.discipline_id == discipline_id,    # WIP matching discipline → show
                )
            )

        query = query.order_by(CdeFolder.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class CdeGroupRepository(BaseRepository[CdeGroup]):

    def __init__(self, session: AsyncSession):
        super().__init__(CdeGroup, session)

    async def list_by_project(
        self,
        owner_type: str,
        owner_id: UUID,
    ) -> list[CdeGroup]:
        query = (
            select(CdeGroup)
            .where(
                CdeGroup.owner_type == owner_type,
                CdeGroup.owner_id == owner_id,
                CdeGroup.deleted_at.is_(None),
            )
            .order_by(CdeGroup.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_group(
        self,
        owner_type: str,
        owner_id: UUID,
        name: str,
        file_ids: list[UUID],
        description: str | None,
        created_by: UUID,
    ) -> CdeGroup:
        group = CdeGroup(
            owner_type=owner_type,
            owner_id=owner_id,
            name=name,
            description=description,
            file_ids=[str(fid) for fid in file_ids],
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(group)
        await self.session.flush()
        return group

    async def update_group(
        self,
        group_id: UUID,
        name: str | None = None,
        description: str | None = None,
        file_ids: list[UUID] | None = None,
        updated_by: UUID | None = None,
    ) -> CdeGroup | None:
        values: dict = {}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description
        if file_ids is not None:
            values["file_ids"] = [str(fid) for fid in file_ids]
        if updated_by is not None:
            values["updated_by"] = updated_by
        values["updated_at"] = datetime.now(timezone.utc)

        await self.session.execute(
            update(CdeGroup)
            .where(CdeGroup.id == group_id, CdeGroup.deleted_at.is_(None))
            .values(**values)
        )
        await self.session.flush()
        return await self.get_by_id(group_id)

    async def soft_delete(self, group_id: UUID, deleted_by: UUID) -> None:
        await self.session.execute(
            update(CdeGroup)
            .where(CdeGroup.id == group_id)
            .values(
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
                updated_at=datetime.now(timezone.utc),
                updated_by=deleted_by,
            )
        )
        await self.session.flush()