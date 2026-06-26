import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus
from app.repositories import action_repo
from app.schemas.action import ActionRead
from app.schemas.pagination import CursorPage


async def create_action(
    session: AsyncSession,
    device_id: uuid.UUID,
    action_type: str,
    payload: dict,
    idempotency_key: str,
    created_by: str,
) -> tuple[ActionRead, bool]:
    action, was_created = await action_repo.create_action_idempotent(
        session=session,
        device_id=device_id,
        idempotency_key=idempotency_key,
        action_type=action_type,
        payload=payload,
        created_by=created_by,
    )
    return ActionRead.model_validate(action), was_created


async def list_actions(
    session: AsyncSession,
    device_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 50,
    status: ActionStatus | None = None,
) -> CursorPage[ActionRead]:
    items, next_cursor = await action_repo.list_actions_for_device(
        session=session,
        device_id=device_id,
        cursor=cursor,
        limit=limit,
        status=status,
    )
    return CursorPage[ActionRead](
        items=[ActionRead.model_validate(a) for a in items],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


async def transition_action(
    session: AsyncSession,
    action_id: uuid.UUID,
    to_status: ActionStatus,
    expected_current: ActionStatus,
) -> ActionRead:
    action = await action_repo.transition_action(
        session=session,
        action_id=action_id,
        to_status=to_status,
        expected_current=expected_current,
    )
    return ActionRead.model_validate(action)
