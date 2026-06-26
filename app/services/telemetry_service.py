import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.repositories import device_repo, telemetry_repo
from app.schemas.telemetry import TelemetryRead, TelemetryWrite


async def ingest_telemetry(
    session: AsyncSession,
    device_id: uuid.UUID,
    records: list[TelemetryWrite],
) -> int:
    payloads: list[dict] = []
    for r in records:
        payloads.append(
            {
                "device_id": device_id,
                "recorded_at": r.recorded_at,
                "battery_level": r.battery_level,
                "lat": r.lat,
                "lng": r.lng,
                "altitude": r.altitude,
                "signal_strength": r.signal_strength,
                "cpu_temp": r.cpu_temp,
                "payload": r.payload,
            }
        )

    inserted = await telemetry_repo.upsert_telemetry(session, payloads)

    latest_recorded_at = max(r.recorded_at for r in records)
    await device_repo.update_device_last_seen(session, device_id, latest_recorded_at)

    return inserted


async def get_telemetry_for_device(
    session: AsyncSession,
    device_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 100,
) -> tuple[Sequence[TelemetryRead], str | None]:
    dt_cursor: datetime | None = None
    if cursor:
        dt_cursor = datetime.fromisoformat(cursor)

    items, next_dt = await telemetry_repo.list_telemetry_for_device(
        session, device_id, cursor=dt_cursor, limit=limit
    )

    next_cursor: str | None = next_dt.isoformat() if next_dt else None
    return (
        [TelemetryRead.model_validate(t) for t in items],
        next_cursor,
    )


from datetime import datetime
