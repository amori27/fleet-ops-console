import hashlib

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.models.device import Device


class DeviceAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code


async def get_current_device(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Device:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise DeviceAuthError("Missing X-API-Key header")

    hashed = hashlib.sha256(api_key.encode()).hexdigest()
    device = await session.scalar(
        select(Device).where(Device.api_key_hash == hashed)
    )
    if not device:
        raise DeviceAuthError("Invalid API key")
    return device
