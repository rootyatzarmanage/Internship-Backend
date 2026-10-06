import logging
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from ycpa.repositories.activity_log import ActivityLogRepository
from ycpa.schemas.responses.activity_log import ActivityLogItemResponse,ActivityLogResponse

logger = logging.getLogger(__name__)


ActivityLogFilter = Literal[
    "all",
    "projects",
    "meetings",
    "workspaces",
]


class ActivityLogService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.repository = ActivityLogRepository(session)

    @staticmethod
    def _get_category(
        resource_type: str | None,
        action: str | None,
    ) -> ActivityLogFilter | None:

        resource = (
            resource_type or ""
        ).lower()

        action_value = (
            action or ""
        ).upper()

        if (
            "project" in resource
            or action_value.startswith("PROJECT_")
        ):
            return "projects"

        if (
            "meeting" in resource
            or action_value.startswith("MEETING_")
        ):
            return "meetings"

        if (
            "workspace" in resource
            or action_value.startswith("WORKSPACE_")
        ):
            return "workspaces"

        return None

    @staticmethod
    def _get_initials(
        full_name: str,
    ) -> str:

        parts = [
            part.strip()
            for part in full_name.split()
            if part.strip()
        ]

        if not parts:
            return "U"

        if len(parts) == 1:
            return parts[0][:2].upper()

        return (
            parts[0][0]
            + parts[-1][0]
        ).upper()

    @staticmethod
    def _relative_time(
        created_at: datetime,
    ) -> str:

        now = datetime.now(timezone.utc)

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        seconds = int(
            (now - created_at).total_seconds()
        )

        if seconds < 60:
            return "Just now"

        minutes = seconds // 60

        if minutes < 60:
            return (
                f"{minutes} min ago"
                if minutes != 1
                else "1 min ago"
            )

        hours = minutes // 60

        if hours < 24:
            return (
                f"{hours} hr ago"
                if hours == 1
                else f"{hours} hrs ago"
            )

        days = hours // 24

        if days == 1:
            return "Yesterday"

        if days < 7:
            return f"{days} days ago"

        return created_at.strftime(
            "%d %b, %I:%M %p"
        )

    @staticmethod
    def _extract_resource_name(
        audit: object,
    ) -> str | None:

        payload = getattr(
            audit,
            "payload",
            None,
        )

        changed_to = getattr(
            audit,
            "changed_to",
            None,
        )

        for data in (
            payload,
            changed_to,
        ):
            if not isinstance(data, dict):
                continue

            for key in (
                "name",
                "project_name",
                "workspace_name",
                "meeting_name",
                "title",
            ):
                value = data.get(key)

                if value:
                    return str(value)

        return None

    @staticmethod
    def _build_message(
        actor_name: str,
        action: str,
        resource_name: str | None,
        category: str,
    ) -> str:

        action_text = (
            action
            .replace("_", " ")
            .lower()
        )

        if resource_name:
            return (
                f"{actor_name} "
                f"{action_text} "
                f"{resource_name}"
            )

        return (
            f"{actor_name} "
            f"{action_text}"
        )

    async def get_activity_logs(
        self,
        current_user,
        category: ActivityLogFilter = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> ActivityLogResponse:

        rows, total = (
            await self.repository.get_activity_logs(
                user_id=current_user.id,
                category=category,
                limit=limit,
                offset=offset,
            )
        )

        activities = []

        for audit, user in rows:

            resolved_category = (
                self._get_category(
                    resource_type=audit.resource_type,
                    action=audit.action,
                )
            )

            if resolved_category is None:
                continue

            actor_name = (
                user.full_name
                if user
                else "Unknown User"
            )

            resource_name = (
                self._extract_resource_name(
                    audit
                )
            )

            activities.append(
                ActivityLogItemResponse(
                    id=audit.id,

                    actor_id=str(
                        audit.user_id
                    ),

                    actor_name=actor_name,

                    actor_initials=(
                        self._get_initials(
                            actor_name
                        )
                    ),

                    action=audit.action,

                    resource_type=(
                        audit.resource_type
                    ),

                    resource_id=(
                        audit.resource_id
                    ),

                    resource_name=(
                        resource_name
                    ),

                    category=(
                        resolved_category
                    ),

                    workspace_id=(
                        str(audit.workspace_id)
                        if audit.workspace_id
                        else None
                    ),

                    workspace_name=None,

                    project_id=(
                        str(audit.project_id)
                        if audit.project_id
                        else None
                    ),

                    project_name=None,

                    created_at=(
                        audit.created_at
                    ),

                    relative_time=(
                        self._relative_time(
                            audit.created_at
                        )
                    ),

                    message=(
                        self._build_message(
                            actor_name=actor_name,
                            action=audit.action,
                            resource_name=resource_name,
                            category=resolved_category,
                        )
                    ),
                )
            )

        return ActivityLogResponse(
            filter=category,
            activities=activities,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(
                offset + len(activities)
                < total
            ),
        )