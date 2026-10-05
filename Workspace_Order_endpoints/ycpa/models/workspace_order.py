import uuid
from datetime import datetime,timezone

from sqlalchemy import DateTime,ForeignKey,Integer,UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped,mapped_column

from ycpa.core.database.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class WorkspaceOrder(Base):

    __tablename__ = "workspace_order"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name = "uq_workspace_order_user_workspace"
        ),
        UniqueConstraint(
            "user_id",
            "order_no",
            name = "uq_workspace_order_user_position"
        )
    )
    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4
    )
    workspace_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable = False,
        index = True
    )
    user_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id",ondelete="CASCADE"),
        nullable = False,
        index = True
    )
    order_no : Mapped[int] = mapped_column(
        Integer,
        nullable = False
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = utcnow,
        nullable = False
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable = False
    )