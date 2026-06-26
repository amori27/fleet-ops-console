import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.device_auth import get_current_device
from app.auth.models import Role
from app.auth.ops_auth import get_current_ops_user, require_role
from app.db.engine import get_db
from app.models.device import Device as DeviceORM
from app.schemas.action import ActionCreate, ActionRead
from app.schemas.device import DeviceDetail, DeviceRead
from app.schemas.pagination import CursorPage
from app.schemas.telemetry import TelemetryBatch, TelemetryRead
from app.services import action_service, device_service, telemetry_service

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/devices", response_model=CursorPage[DeviceRead])
async def list_devices(
    cursor: str | None = None,
    limit: int = 50,
    status: str | None = None,
    device_type: str | None = None,
    region: str | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_db),
    _user=Depends(require_role(Role.VIEWER)),
):
    return await device_service.list_devices(
        session=session,
        cursor=cursor,
        limit=limit,
        status=status,
        device_type=device_type,
        region=region,
        search=search,
    )


@router.get("/devices/{device_id}", response_model=DeviceDetail)
async def get_device(
    device_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _user=Depends(require_role(Role.VIEWER)),
):
    detail = await device_service.get_device_detail(session, device_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return detail


@router.post("/telemetry", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    batch: TelemetryBatch,
    request: Request,
    session: AsyncSession = Depends(get_db),
    device: DeviceORM = Depends(get_current_device),
):
    inserted = await telemetry_service.ingest_telemetry(
        session=session,
        device_id=device.id,
        records=batch.records,
    )
    return {"ingested": inserted, "device_id": str(device.id)}


@router.post(
    "/devices/{device_id}/actions",
    response_model=ActionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_action(
    device_id: uuid.UUID,
    action_data: ActionCreate,
    session: AsyncSession = Depends(get_db),
    commander=Depends(require_role(Role.COMMANDER)),
):
    action, was_created = await action_service.create_action(
        session=session,
        device_id=device_id,
        action_type=action_data.action_type,
        payload=action_data.payload,
        idempotency_key=action_data.idempotency_key,
        created_by=commander.username,
    )

    if was_created:
        return action

    return JSONResponse(
        status_code=200,
        content=action.model_dump(mode="json"),
    )


@router.get(
    "/devices/{device_id}/actions",
    response_model=CursorPage[ActionRead],
)
async def list_actions(
    device_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 50,
    status: str | None = None,
    session: AsyncSession = Depends(get_db),
    _user=Depends(require_role(Role.VIEWER)),
):
    from app.models.action import ActionStatus

    action_status = ActionStatus(status) if status else None
    return await action_service.list_actions(
        session=session,
        device_id=device_id,
        cursor=cursor,
        limit=limit,
        status=action_status,
    )
