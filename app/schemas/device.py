import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    device_type: str
    hardware_version: str
    region: str | None
    status: str
    last_seen: datetime | None
    created_at: datetime


class DeviceDetail(DeviceRead):
    latest_telemetry: "TelemetryRead | None" = None


class DeviceFilter(BaseModel):
    status: str | None = None
    device_type: str | None = None
    region: str | None = None
    search: str | None = None


from app.schemas.telemetry import TelemetryRead  # noqa: E402, F811

DeviceDetail.model_rebuild()
