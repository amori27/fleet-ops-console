import base64
import json
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


def _decode_cursor(cursor: str) -> dict:
    decoded = json.loads(base64.urlsafe_b64decode(cursor).decode())
    return decoded


def _encode_cursor(device: Device) -> str:
    cursor_data = {
        "status": device.status,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "id": str(device.id),
    }
    return base64.urlsafe_b64encode(
        json.dumps(cursor_data, sort_keys=True).encode()
    ).decode()


def _apply_filters(query: Select, **filters) -> Select:
    if filters.get("status"):
        query = query.where(Device.status == filters["status"])
    if filters.get("device_type"):
        query = query.where(Device.device_type == filters["device_type"])
    if filters.get("region"):
        query = query.where(Device.region == filters["region"])
    if filters.get("search"):
        tsquery = func.plainto_tsquery("english", filters["search"])
        tsvector = func.to_tsvector(
            "english",
            Device.name + " " + func.coalesce(Device.region, ""),
        )
        query = query.where(tsvector.op("@@")(tsquery))
    return query


async def list_devices(
    session: AsyncSession,
    cursor: str | None = None,
    limit: int = 50,
    status: str | None = None,
    device_type: str | None = None,
    region: str | None = None,
    search: str | None = None,
) -> tuple[Sequence[Device], str | None]:
    query = select(Device).where(Device.status != "decommissioned")

    if cursor:
        decoded = _decode_cursor(cursor)
        cursor_status = decoded["status"]
        cursor_last_seen = (
            datetime.fromisoformat(decoded["last_seen"])
            if decoded.get("last_seen")
            else None
        )
        cursor_id = uuid.UUID(decoded["id"])

        query = query.where(
            or_(
                (Device.status == cursor_status)
                & (Device.last_seen < cursor_last_seen),
                (Device.status == cursor_status)
                & (Device.last_seen == cursor_last_seen)
                & (Device.id > cursor_id),
            )
        )

    query = _apply_filters(
        query, status=status, device_type=device_type, region=region, search=search
    )

    query = query.order_by(
        Device.status.asc(),
        Device.last_seen.desc().nulls_last(),
        Device.id.asc(),
    ).limit(limit + 1)

    result = await session.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    items = list(rows[:limit])

    next_cursor: str | None = None
    if has_more and items:
        next_cursor = _encode_cursor(items[-1])

    return items, next_cursor


async def get_device(
    session: AsyncSession, device_id: uuid.UUID
) -> Device | None:
    return await session.scalar(select(Device).where(Device.id == device_id))


async def update_device_last_seen(
    session: AsyncSession, device_id: uuid.UUID, recorded_at: datetime
) -> None:
    await session.execute(
        update(Device)
        .where(Device.id == device_id)
        .where(
            or_(
                Device.last_seen.is_(None),
                Device.last_seen < recorded_at,
            )
        )
        .values(last_seen=recorded_at)
    )
