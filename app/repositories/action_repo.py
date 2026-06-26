import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus


async def create_action_idempotent(
    session: AsyncSession,
    device_id: uuid.UUID,
    idempotency_key: str,
    action_type: str,
    payload: dict,
    created_by: str,
) -> tuple[Action, bool]:
    stmt = pg_insert(Action).values(
        idempotency_key=idempotency_key,
        device_id=device_id,
        action_type=action_type,
        payload=payload,
        created_by=created_by,
        status=ActionStatus.PENDING,
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["idempotency_key"],
    )
    stmt = stmt.returning(Action)
    result = await session.execute(stmt)
    action = result.scalar_one_or_none()

    if action is not None:
        await session.commit()
        return action, True

    existing = await session.scalar(
        select(Action).where(Action.idempotency_key == idempotency_key)
    )
    assert existing is not None
    return existing, False


async def transition_action(
    session: AsyncSession,
    action_id: uuid.UUID,
    to_status: ActionStatus,
    expected_current: ActionStatus,
) -> Action:
    result = await session.execute(
        update(Action)
        .where(Action.id == action_id, Action.status == expected_current)
        .values(status=to_status)
        .returning(Action)
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise ValueError(
            f"Cannot transition action {action_id} from "
            f"{expected_current.value} to {to_status.value}: "
            f"current status does not match expected or action not found"
        )
    await session.commit()
    return action


async def list_actions_for_device(
    session: AsyncSession,
    device_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 50,
    status: ActionStatus | None = None,
) -> tuple[Sequence[Action], str | None]:
    query = (
        select(Action)
        .where(Action.device_id == device_id)
        .order_by(Action.created_at.desc(), Action.id.desc())
        .limit(limit + 1)
    )

    if status:
        query = query.where(Action.status == status)

    if cursor:
        cursor_id = uuid.UUID(cursor)
        query = query.where(Action.id < cursor_id)

    result = await session.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    items = list(rows[:limit])
    next_cursor: str | None = None
    if has_more and items:
        next_cursor = str(items[-1].id)

    return items, next_cursor


async def get_action(
    session: AsyncSession, action_id: uuid.UUID
) -> Action | None:
    return await session.scalar(select(Action).where(Action.id == action_id))
