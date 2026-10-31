import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.email import build_notification_email, send_email
from ycpa.models.control_panel import ControlPanel

logger = logging.getLogger(__name__)

MAIL_SLUGS = {
    "error":         "Mail-Settings/Manage-Error-Mail",
    "user_register": "Mail-Settings/User-Register-Mail",
    "workspace":     "Mail-Settings/Workspace-Notification-Mail",
    "payment":       "Mail-Settings/Payment-Notification",
    "project":       "Mail-Settings/Project-Notification",
    "ticket":        "Mail-Settings/Ticket-Notification",
}
_tasks: set = set()


async def notify(session: AsyncSession, key: str, subject: str, rows: dict) -> bool:
    """Never raises: a mail problem must not break the request."""
    try:
        cfg = await session.scalar(select(ControlPanel.value_json).where(
            ControlPanel.slug == MAIL_SLUGS[key], ControlPanel.deleted_at.is_(None)))
        if not cfg or not cfg.get("email"):
            return False
        task = asyncio.create_task(
            send_email(cfg["email"], subject, build_notification_email(subject, rows), cc=cfg.get("cc") or []))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
        return True
    except Exception:
        logger.exception("Notification failed", extra={"key": key})
        return False
