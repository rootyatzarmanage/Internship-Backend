import logging
from datetime import datetime, timezone
from typing import Optional
 
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from ycpa.core.auth.jwt_verifier import get_jwt_verifier
from ycpa.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
)
from ycpa.models.platform_permission import UserPlatformPermission
from ycpa.models.storage_usage import StorageUsage
from ycpa.models.subscription import AimSubscription, PimSubscription
from ycpa.models.user import User
from ycpa.repositories.auth.users import UserRepository
from ycpa.schemas.responses.auth import LoginResponse, UserProfileResponse
from ycpa.services.base import BaseService
 
logger = logging.getLogger(__name__)
 
 
class AuthService(BaseService):
 
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.user_repo = UserRepository(session)
 
 
    async def login(
        self,
        id_token: str,
        ip_address: Optional[str] = None,
    ) -> LoginResponse:
        from uuid import UUID
        verifier = get_jwt_verifier()
        try:
            claims = await verifier.verify_token(id_token)
        except Exception as e:
            logger.warning("JWT verification failed", extra={"error": str(e), "ip": ip_address})
            raise UnauthorizedException("Invalid or expired token")
 
        user_id = claims.get("sub")
        if not user_id:
            raise UnauthorizedException("Token missing required claims")
 
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user:
            raise UnauthorizedException("User not found")
 
        self.require_active_user(user)
        user = await self.user_repo.update_by_id(user.id, {
            "last_login_at": datetime.now(timezone.utc),
            "last_login_ip": ip_address,
            "login_count":   (user.login_count or 0) + 1,
        })
        logger.info("User logged in", extra={"user_id": str(user.id), "email": user.email})
 
        await self.log_audit(
            action="USER_LOGIN",
            resource_type="user",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=ip_address,
            payload={"email": user.email},
        )
 
        await self.session.commit()
 
        try:
            perm_result = await self.session.execute(
                select(UserPlatformPermission.permission_slug).where(
                    UserPlatformPermission.user_id == user.id
                )
            )
            permissions = [row[0] for row in perm_result.all()]
        except Exception:
            await self.session.rollback()
            logger.warning(
                "user_platform_permissions table missing or query failed — "
                "returning empty permissions",
                extra={"user_id": str(user.id)},
            )
            permissions = []
 
        profile = UserProfileResponse.model_validate(user)
        profile.platform_permissions = permissions
 
        return LoginResponse(
            user=profile,
            is_new_user=False,
        )
 
 
    async def get_me(self, user_id: str) -> UserProfileResponse:
        from uuid import UUID
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user:
            raise NotFoundException("User not found")
 
        perm_result = await self.session.execute(
            select(UserPlatformPermission.permission_slug).where(
                UserPlatformPermission.user_id == user.id
            )
        )
        permissions = [row[0] for row in perm_result.all()]
 
        profile = UserProfileResponse.model_validate(user)
        profile.platform_permissions = permissions
        return profile
 
 
    async def update_profile(
        self,
        user_id: str,
        full_name:    Optional[str] = None,
        company_name: Optional[str] = None,
        job_title:    Optional[str] = None,
        phone:        Optional[str] = None,
        timezone:     Optional[str] = None,
    ) -> UserProfileResponse:
        from uuid import UUID
        uid = UUID(user_id)
 
        values = {}
        if full_name    is not None: values["full_name"]    = full_name
        if company_name is not None: values["company_name"] = company_name
        if job_title    is not None: values["job_title"]    = job_title
        if phone        is not None: values["phone"]        = phone
        if timezone     is not None: values["timezone"]     = timezone
 
        if not values:
            user = await self.user_repo.get_by_id(uid)
            return UserProfileResponse.model_validate(user)
 
        if "full_name" in values:
            values["is_onboarded"] = True
 
        user = await self.user_repo.update_by_id(uid, values)
 
        await self.log_audit(
            action="USER_PROFILE_UPDATED",
            resource_type="user",
            resource_id=str(uid),
            user_id=uid,
            payload={"updated_fields": list(values.keys())},
        )
 
        await self.session.commit()
        return UserProfileResponse.model_validate(user)
 
 
    async def logout(self, user, ip_address: Optional[str] = None) -> None:
        await self.log_audit(
            action="USER_LOGOUT",
            resource_type="user",
            resource_id=str(user.id),
            user_id=user.id,
            ip_address=ip_address,
            payload={"email": user.email},
        )
        await self.session.commit()
        logger.info("User logged out", extra={"user_id": str(user.id)})
 
 
    async def _create_user(
        self,
        cognito_sub: str,
        email: str,
        email_verified: bool,
    ) -> User:
        existing = await self.user_repo.get_by_email(email)
        if existing:
 
            logger.warning(
                "Email collision on signup — linking new cognito_sub to existing account",
                extra={"user_id": str(existing.id), "email": email},
            )
            linked = await self.user_repo.update_by_id(existing.id, {
                "cognito_sub":    cognito_sub,
                "email_verified": email_verified,
            })
            await self.session.flush()
            return linked
 
        user = User(
            cognito_sub=cognito_sub,
            email=email,
            email_verified=email_verified,
            full_name=email.split("@")[0],
            platform_role="customer",
            is_active=True,
            is_onboarded=False,
            login_count=1,
            last_login_at=datetime.now(timezone.utc),
            created_by=None,
        )
        user = await self.user_repo.create(user)
 
        self.session.add(StorageUsage(
            user_id=user.id,
            bytes_used=0,
            bytes_limit=5_368_709_120,
            file_count=0,
        ))
 
        self.session.add(PimSubscription(
            user_id=user.id,
            plan="free",
            status="active",
            max_pim_workspaces=1,
            max_projects_per_pim_workspace=1,
            max_members_per_workspace=10,
            max_members_per_project=10,
            can_use_4d=False,
            can_use_5d=False,
            can_use_clash_detection=False,
            can_export_bcf=True,
            can_use_api=False,
        ))
 
        self.session.add(AimSubscription(
            user_id=user.id,
            plan="free",
            status="active",
            max_aim_workspaces=1,
            max_projects_per_aim_workspace=1,
            max_members_per_workspace=10,
            max_members_per_project=10,
            can_use_ai=False,
            can_use_api=False,
            can_use_maintenance=True,
            can_use_facility=True,
        ))
 
        await self.session.flush()
 
        logger.info(
            "User + storage + subscriptions created",
            extra={"user_id": str(user.id), "email": email},
        )
        return user