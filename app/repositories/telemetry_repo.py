import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, literal_column, select
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
    # ``xmax = 0`` marks rows this statement inserted; updated rows carry a
    # non-zero xmax. The caller owns the transaction (get_db / test fixture)
    # so a later failed write can still roll the whole batch back.
    stmt = stmt.returning(
        TelemetryEvent.id,
        literal_column("xmax = 0").label("was_insert"),
    )
    result = await session.execute(stmt)

    return sum(1 for row in result if row[1])


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
