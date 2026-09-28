import logging
from datetime import datetime, timezone,date
from uuid import UUID

from sqlalchemy import (
    String,
    and_,
    case,
    cast,
    distinct,
    func,
    or_,
    select,
)

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.models.audit import AuditLog
from ycpa.models.user import User
from ycpa.models.workspace import (
    PimWorkspace,
    PimWorkspaceMember,
    PimProject,
    PimProjectMember,
    AimWorkspace,
    AimWorkspaceMember,
    AimProject,
    AimProjectMember,
)

logger = logging.getLogger(__name__)


class AdminUserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_total_users(self) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None)
        )

        result = await self.session.execute(query)

        return int(result.scalar() or 0)

    async def get_users_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(
            func.count(User.id)
        ).where(
            User.deleted_at.is_(None),
            User.created_at >= start_date,
            User.created_at < end_date,
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_active_users(self) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_active_users_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            User.created_at >= start_date,
            User.created_at < end_date,
        )

        result = await self.session.execute(query)
        return int(result.scalar() or 0)
    
    async def get_verified_users(self) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.email_verified.is_(True),
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)


    async def get_verified_users_between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.email_verified.is_(True),
            User.created_at >= start_date,
            User.created_at < end_date,
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_new_signups(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:

        query = select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.created_at >= start_date,
            User.created_at < end_date,
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_users(
        self,
        search: str | None = None,
        name: str | None = None,
        email: str | None = None,
        verified: bool | None = None,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 6,
        offset: int = 0,
    ):

        pim_workspace_ids = (
            select(
                PimWorkspace.id.label("workspace_id")
            )
            .where(
                PimWorkspace.owner_id == User.id,
                PimWorkspace.deleted_at.is_(None),
            )
            .correlate(User)
        )
        pim_member_workspace_ids = (
            select(
                PimWorkspaceMember.workspace_id.label("workspace_id")
            )
            .where(
                PimWorkspaceMember.user_id == User.id,
                PimWorkspaceMember.workspace_id.in_(
                    select(PimWorkspace.id).where(
                        PimWorkspace.deleted_at.is_(None)
                    )
                ),
            )
            .correlate(User)
        )
        pim_workspace_count = (
            select(
                func.count(
                    distinct(
                        cast(
                            pim_workspace_ids.c.workspace_id,
                            String,
                        )
                    )
                )
            )
        )

        pim_owned_count = (
            select(
                func.count(PimWorkspace.id)
            )
            .where(
                PimWorkspace.owner_id == User.id,
                PimWorkspace.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        pim_member_count = (
            select(
                func.count(
                    distinct(PimWorkspaceMember.workspace_id)
                )
            )
            .where(
                PimWorkspaceMember.user_id == User.id,
                PimWorkspaceMember.workspace_id.in_(
                    select(PimWorkspace.id).where(
                        PimWorkspace.deleted_at.is_(None)
                    )
                ),
            )
            .correlate(User)
            .scalar_subquery()
        )

        aim_owned_count = (
            select(
                func.count(AimWorkspace.id)
            )
            .where(
                AimWorkspace.owner_id == User.id,
                AimWorkspace.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        aim_member_count = (
            select(
                func.count(
                    distinct(
                        AimWorkspaceMember.workspace_id
                    )
                )
            )
            .where(
                AimWorkspaceMember.user_id == User.id,
                AimWorkspaceMember.workspace_id.in_(
                    select(AimWorkspace.id).where(
                        AimWorkspace.deleted_at.is_(None)
                    )
                ),
            )
            .correlate(User)
            .scalar_subquery()
        )

        pim_created_projects = (
            select(
                func.count(PimProject.id)
            )
            .join(
                PimWorkspace,
                PimWorkspace.id == PimProject.workspace_id,
            )
            .where(
                PimProject.created_by == User.id,
                PimProject.deleted_at.is_(None),
                PimWorkspace.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        pim_member_projects = (
            select(
                func.count(
                    distinct(PimProjectMember.project_id)
                )
            )
            .join(
                PimProject,
                PimProject.id == PimProjectMember.project_id,
            )
            .where(
                PimProjectMember.user_id == User.id,
                PimProject.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        aim_created_projects = (
            select(func.count(AimProject.id))
            .join(
                AimWorkspace,
                AimWorkspace.id == AimProject.workspace_id,
            )
            .where(
                AimProject.created_by == User.id,
                AimProject.deleted_at.is_(None),
                AimWorkspace.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        aim_member_projects = (
            select(
                func.count(
                    distinct(AimProjectMember.project_id)
                )
            )
            .join(
                AimProject,
                AimProject.id == AimProjectMember.project_id,
            )
            .where(
                AimProjectMember.user_id == User.id,
                AimProject.deleted_at.is_(None),
            )
            .correlate(User)
            .scalar_subquery()
        )

        workspace_count = (
            pim_owned_count
            + pim_member_count
            + aim_owned_count
            + aim_member_count
        )

        project_count = (
            pim_created_projects
            + pim_member_projects
            + aim_created_projects
            + aim_member_projects
        )

        latest_auth_action = (
            select(AuditLog.action)
            .where(
                AuditLog.user_id == User.id,
                AuditLog.action.in_(
                    [
                        "USER_LOGIN",
                        "USER_LOGOUT",
                    ]
                ),
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(1)
            .correlate(User)
            .scalar_subquery()
        )

        user_status = case(
            (
                or_(
                    User.is_active.is_(False),
                    User.deactivated_at.is_not(None),
                ),
                "Deactive",
            ),
            (
                latest_auth_action == "USER_LOGIN",
                "Active",
            ),
            else_="Offline",
        ).label("status")

        query = select(
            User.id,
            User.full_name,
            User.email,
            User.phone,
            User.email_verified,
            User.last_login_at,
            User.created_at,
            workspace_count.label("workspace_count"),
            project_count.label("project_count"),
            user_status,
        ).where(
            User.deleted_at.is_(None)
        )

        if search:

            search_value = search.strip()
            query = query.where(
                or_(
                    cast(
                        User.id,
                        String,
                    ).ilike(
                        f"%{search_value}%"
                    ),

                    User.full_name.ilike(
                        f"%{search_value}%"
                    ),

                    User.email.ilike(
                        f"%{search_value}%"
                    ),
                )
            )
        if name:
            query = query.where(
                User.full_name.ilike(
                    f"%{name.strip()}%"
                )
            )

        if email:
            query = query.where(
                User.email.ilike(
                    f"%{email.strip()}%"
                )
            )

        if verified is not None:
            query = query.where(
                User.email_verified.is_(verified)
            )

        if status:
            query = query.where(
                user_status == status
            )
        if start_date:
            query = query.where(
            User.created_at >= start_date
        )
        if end_date:
            query = query.where(
                User.created_at < end_date.fromordinal(
                end_date.toordinal() + 1
            )
        )

        query = (
            query
            .order_by(
                User.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.all()


    async def count_users(
        self,
        search: str | None = None,
        name: str | None = None,
        email: str | None = None,
        verified: bool | None = None,
        status: str | None = None,
    ) -> int:
        latest_auth_action = (
            select(AuditLog.action)
            .where(
                AuditLog.user_id == User.id,
                AuditLog.action.in_(
                    [
                        "USER_LOGIN",
                        "USER_LOGOUT",
                    ]
                ),
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(1)
            .correlate(User)
            .scalar_subquery()
        )

        user_status = case(
            (
                or_(
                    User.is_active.is_(False),
                    User.deactivated_at.is_not(None),
                ),
                "Deactive",
            ),
            (
                latest_auth_action == "USER_LOGIN",
                "Active",
            ),
            else_="Offline",
        )

        query = select(
            func.count(User.id)
        ).where(
            User.deleted_at.is_(None)
        )

        if search:
            search_value = search.strip()

            query = query.where(
                or_(
                    cast(
                        User.id,
                        String,
                    ).ilike(
                        f"%{search_value}%"
                    ),
                    User.full_name.ilike(
                        f"%{search_value}%"
                    ),
                    User.email.ilike(
                        f"%{search_value}%"
                    ),
                )
            )

        if name:
            query = query.where(
                User.full_name.ilike(
                    f"%{name.strip()}%"
                )
            )

        if email:
            query = query.where(
                User.email.ilike(
                    f"%{email.strip()}%"
                )
            )

        if verified is not None:
            query = query.where(
                User.email_verified.is_(verified)
            )

        if status:
            query = query.where(user_status == status)

        result = await self.session.execute(query)
        return int(result.scalar() or 0)

    async def get_verified_status_by_year(
        self,
        year: int,
    ):

        query = select(
            func.extract(
                "month",
                User.created_at,
            ).label("month"),

            func.count(
                case(
                    (
                        User.email_verified.is_(True),
                        1,
                    )
                )
            ).label("verified"),

            func.count(
                case(
                    (
                        User.email_verified.is_(False),
                        1,
                    )
                )
            ).label("not_verified"),

        ).where(
            User.deleted_at.is_(None),

            func.extract(
                "year",
                User.created_at,
            ) == year,

        ).group_by(
            func.extract(
                "month",
                User.created_at,
            )
        ).order_by(
            func.extract(
                "month",
                User.created_at,
            )
        )

        result = await self.session.execute(query)

        return result.all()

    async def get_users_by_status(self):

        latest_auth_action = (
            select(
                AuditLog.action
            )
            .where(
                AuditLog.user_id == User.id,
                AuditLog.action.in_(
                    [
                        "USER_LOGIN",
                        "USER_LOGOUT",
                    ]
                ),
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(1)
            .correlate(User)
            .scalar_subquery()
        )

        derived_status = case(
            (
                or_(
                    User.is_active.is_(False),
                    User.deactivated_at.is_not(None),
                ),
                "Deactive",
            ),
            (
                latest_auth_action== "USER_LOGIN","Active",
            ),
            else_="Offline",
        ).label("status")

        query = select(
            derived_status,
            func.count(User.id).label(
                "count"
            ),
        ).where(
            User.deleted_at.is_(None)
        ).group_by(
            derived_status
        )
        result = await self.session.execute(query)
        return result.all()