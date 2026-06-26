import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        UniqueConstraint("device_id", "recorded_at", name="uq_telemetry_device_time"),
        CheckConstraint(
            "battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100)",
            name="ck_telemetry_battery_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id"), index=True
    )
    recorded_at: Mapped[datetime]
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())
    battery_level: Mapped[float | None]
    lat: Mapped[float | None]
    lng: Mapped[float | None]
    altitude: Mapped[float | None]
    signal_strength: Mapped[float | None]
    cpu_temp: Mapped[float | None]
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
