import uuid

from app.db.engine import async_session_factory
from app.repositories.action_repo import transition_action
from app.models.action import ActionStatus
from app.services.pubsub import PubSub


async def dispatch_action(ctx: dict, action_id: str, device_id: str, payload: dict) -> bool:
    session = async_session_factory()
    try:
        action_uuid = uuid.UUID(action_id)
        device_uuid = uuid.UUID(device_id)

        action = await transition_action(
            session,
            action_id=action_uuid,
            to_status=ActionStatus.SENT,
            expected_current=ActionStatus.PENDING,
        )

        pubsub = ctx.get("pubsub")
        if pubsub is not None:
            await pubsub.publish(
                f"fleet:actions:{device_id}",
                {
                    "action_id": action_id,
                    "device_id": device_id,
                    "status": "SENT",
                    "action_type": action.action_type,
                },
            )

        return True
    except ValueError:
        return False
    finally:
        await session.close()
