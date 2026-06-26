import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.repositories import device_repo, telemetry_repo
from app.schemas.device import DeviceDetail, DeviceRead
from app.schemas.pagination import CursorPage
from app.schemas.telemetry import TelemetryRead


async def list_devices(
    session: AsyncSession,
    cursor: str | None = None,
    limit: int = 50,
    status: str | None = None,
    device_type: str | None = None,
    region: str | None = None,
    search: str | None = None,
) -> CursorPage[DeviceRead]:
    items, next_cursor = await device_repo.list_devices(
        session=session,
        cursor=cursor,
        limit=limit,
        status=status,
        device_type=device_type,
        region=region,
        search=search,
    )
    return CursorPage[DeviceRead](
        items=[DeviceRead.model_validate(d) for d in items],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


async def get_device_detail(
    session: AsyncSession, device_id: uuid.UUID
) -> DeviceDetail | None:
    device = await device_repo.get_device(session, device_id)
    if device is None:
        return None

    latest = await telemetry_repo.get_latest_telemetry(session, device_id)
    return DeviceDetail(
        **DeviceRead.model_validate(device).model_dump(),
        latest_telemetry=TelemetryRead.model_validate(latest) if latest else None,
    )
