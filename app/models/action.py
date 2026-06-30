import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACK = "ACK"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id")
    )
    idempotency_key: Mapped[str] = mapped_column(unique=True, nullable=False)
    action_type: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[ActionStatus] = mapped_column(default=ActionStatus.PENDING)
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
