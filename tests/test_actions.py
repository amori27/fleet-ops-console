import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus
from app.repositories.action_repo import (
    create_action_idempotent,
    transition_action,
)


class TestActionIdempotency:
    async def test_identical_request_returns_existing_action(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        payload = {
            "device_id": device.id,
            "idempotency_key": "test-key-001",
            "action_type": "reboot",
            "payload": {"graceful": True},
            "created_by": "test-commander",
        }

        action1, created1 = await create_action_idempotent(
            async_session, **payload
        )
        assert created1 is True

        action2, created2 = await create_action_idempotent(
            async_session, **payload
        )
        assert created2 is False
        assert action2.id == action1.id

    async def test_different_keys_create_separate_actions(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        action1, _ = await create_action_idempotent(
            async_session,
            device_id=device.id,
            idempotency_key="key-1",
            action_type="reboot",
            payload={},
            created_by="commander",
        )
        action2, _ = await create_action_idempotent(
            async_session,
            device_id=device.id,
            idempotency_key="key-2",
            action_type="reboot",
            payload={},
            created_by="commander",
        )
        assert action1.id != action2.id

    async def test_idempotency_persists_across_retries(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        payload = {
            "device_id": device.id,
            "idempotency_key": "retry-key-001",
            "action_type": "update_software",
            "payload": {"version": "3.2.1"},
            "created_by": "test-commander",
        }

        action1, created1 = await create_action_idempotent(
            async_session, **payload
        )
        assert created1 is True

        for _ in range(3):
            action_n, created_n = await create_action_idempotent(
                async_session, **payload
            )
            assert created_n is False
            assert action_n.id == action1.id

    async def test_state_machine_valid_transition(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        action, _ = await create_action_idempotent(
            async_session,
            device_id=device.id,
            idempotency_key="sm-key-1",
            action_type="reboot",
            payload={},
            created_by="commander",
        )

        updated = await transition_action(
            async_session,
            action_id=action.id,
            to_status=ActionStatus.SENT,
            expected_current=ActionStatus.PENDING,
        )
        assert updated.status == ActionStatus.SENT

    async def test_state_machine_invalid_transition_raises(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        action, _ = await create_action_idempotent(
            async_session,
            device_id=device.id,
            idempotency_key="sm-key-2",
            action_type="reboot",
            payload={},
            created_by="commander",
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            await transition_action(
                async_session,
                action_id=action.id,
                to_status=ActionStatus.EXECUTED,
                expected_current=ActionStatus.SENT,
            )
