import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TelemetryWrite(BaseModel):
    recorded_at: datetime
    battery_level: float | None = Field(None, ge=0, le=100)
    lat: float | None = None
    lng: float | None = None
    altitude: float | None = None
    signal_strength: float | None = None
    cpu_temp: float | None = None
    payload: dict = Field(default_factory=dict)


class TelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: uuid.UUID
    recorded_at: datetime
    received_at: datetime
    battery_level: float | None
    lat: float | None
    lng: float | None
    altitude: float | None
    signal_strength: float | None
    cpu_temp: float | None
    payload: dict


class TelemetryBatch(BaseModel):
    records: list[TelemetryWrite] = Field(max_length=500)
