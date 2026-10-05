import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    QuotaExceededException,
    UnauthorizedException,
)

logger = logging.getLogger(__name__)


class BaseService:


    def __init__(self, session: AsyncSession):
        self.session = session


    def require_authenticated(self, current_user_id: Optional[UUID]) -> UUID:
        if not current_user_id:
            raise UnauthorizedException("Authentication required")
        return current_user_id

    def require_active_user(self, user) -> None:
        if not user:
            raise NotFoundException("User not found")
        if not user.is_active:
            raise ForbiddenException("Your account has been deactivated")
        if user.deleted_at is not None:
            raise ForbiddenException("Account no longer exists")

    def require_platform_role(self, user, required_role: str) -> None:
        if user.platform_role != required_role:
            raise ForbiddenException(f"This action requires {required_role} role")

    def require_owner_or_admin(
        self,
        resource_owner_id: UUID,
        current_user_id: UUID,
        user_role: str,
        admin_role: str = "admin",
    ) -> None:
        if resource_owner_id != current_user_id and user_role != admin_role:
            raise ForbiddenException("You do not have permission for this action")


    def check_subscription_limit(
        self,
        current_count: int,
        max_allowed: int,
        resource_name: str,
    ) -> None:
        if current_count >= max_allowed:
            raise QuotaExceededException(
                quota_type=resource_name,
                current=current_count,
                limit=max_allowed,
                message=f"You have reached your {resource_name} limit ({max_allowed}). Please upgrade your plan.",
            )


    async def log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        user_id: Optional[UUID],
        *,
        status: str = "success",
        payload: Optional[dict] = None,
        changed_from: Optional[dict] = None,
        changed_to: Optional[dict] = None,
        workspace_type: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:

        try:
            from datetime import datetime, timezone

            from ycpa.models.audit import AuditLog

            self.session.add(AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                status=status,
                workspace_type=workspace_type,
                workspace_id=workspace_id,
                project_id=project_id,
                ip_address=ip_address,
                user_agent=user_agent,
                payload=payload,
                changed_from=changed_from,
                changed_to=changed_to,
                created_at=datetime.now(timezone.utc),
            ))
            await self.session.flush()

            logger.debug(
                "Audit log written",
                extra={
                    "action":        action,
                    "resource_type": resource_type,
                    "resource_id":   str(resource_id) if resource_id else None,
                    "user_id":       str(user_id) if user_id else None,
                    "status":        status,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to write audit log — non-fatal",
                extra={"action": action, "error": str(e)},
                exc_info=True,
            )
 