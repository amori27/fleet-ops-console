import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import TelemetryEvent


async def upsert_telemetry(
    session: AsyncSession,
    records: list[dict],
) -> int:
    if not records:
        return 0

    stmt = pg_insert(TelemetryEvent).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["device_id", "recorded_at"],
        set_={
            "battery_level": stmt.excluded.battery_level,
            "lat": stmt.excluded.lat,
            "lng": stmt.excluded.lng,
            "altitude": stmt.excluded.altitude,
            "signal_strength": stmt.excluded.signal_strength,
            "cpu_temp": stmt.excluded.cpu_temp,
            "payload": stmt.excluded.payload,
            "received_at": func.now(),
        },
    )
    stmt = stmt.returning(func.xmin(TelemetryEvent.id).label("xmin"))
    result = await session.execute(stmt)
    await session.commit()

    return sum(1 for _ in result)


async def get_latest_telemetry(
    session: AsyncSession, device_id: uuid.UUID
) -> TelemetryEvent | None:
    return await session.scalar(
        select(TelemetryEvent)
        .where(TelemetryEvent.device_id == device_id)
        .order_by(TelemetryEvent.recorded_at.desc())
        .limit(1)
    )


async def list_telemetry_for_device(
    session: AsyncSession,
    device_id: uuid.UUID,
    cursor: datetime | None = None,
    limit: int = 100,
) -> tuple[Sequence[TelemetryEvent], datetime | None]:
    query = (
        select(TelemetryEvent)
        .where(TelemetryEvent.device_id == device_id)
        .order_by(TelemetryEvent.recorded_at.desc(), TelemetryEvent.id.desc())
        .limit(limit + 1)
    )

    if cursor:
        query = query.where(TelemetryEvent.recorded_at < cursor)

    result = await session.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    items = list(rows[:limit])
    next_cursor = rows[-1].recorded_at if has_more and items else None

    return items, next_cursor
