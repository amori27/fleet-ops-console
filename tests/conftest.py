import asyncio
import hashlib
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.action import Action, ActionStatus
from app.models.device import Device
from app.models.telemetry import TelemetryEvent


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fleet_test",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def device_factory(async_session: AsyncSession):
    class DeviceFactory:
        _counter = 0

        async def create(
            self,
            status: str = "active",
            device_type: str = "satellite",
            region: str = "LEO",
            **kwargs,
        ) -> Device:
            DeviceFactory._counter += 1
            api_key = f"key-{DeviceFactory._counter}"
            device = Device(
                id=kwargs.get("id", uuid.uuid4()),
                name=kwargs.get("name", f"sat-{DeviceFactory._counter}"),
                device_type=device_type,
                hardware_version=kwargs.get("hardware_version", "v2.1"),
                region=region,
                status=status,
                api_key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
                last_seen=kwargs.get("last_seen"),
            )
            async_session.add(device)
            await async_session.flush()
            return device

        async def create_batch(
            self,
            count: int,
            status: str = "active",
            device_type: str = "satellite",
            region: str = "LEO",
        ) -> list[Device]:
            devices: list[Device] = []
            for i in range(count):
                device = Device(
                    id=uuid.uuid4(),
                    name=f"sat-{DeviceFactory._counter + i + 1}",
                    device_type=device_type,
                    hardware_version="v2.1",
                    region=region,
                    status=status,
                    api_key_hash=hashlib.sha256(f"key-{i}".encode()).hexdigest(),
                    last_seen=datetime.now(timezone.utc),
                )
                async_session.add(device)
                DeviceFactory._counter += 1
                devices.append(device)
            await async_session.flush()
            return devices

    return DeviceFactory()


@pytest_asyncio.fixture
async def action_factory(async_session: AsyncSession):
    class ActionFactory:
        _counter = 0

        async def create(
            self,
            device_id: uuid.UUID,
            status: ActionStatus = ActionStatus.PENDING,
            created_by: str = "test-commander",
        ) -> Action:
            ActionFactory._counter += 1
            action = Action(
                id=uuid.uuid4(),
                device_id=device_id,
                idempotency_key=f"idem-{ActionFactory._counter}",
                action_type="reboot",
                payload={"graceful": True},
                status=status,
                created_by=created_by,
            )
            async_session.add(action)
            await async_session.flush()
            return action

    return ActionFactory()


@pytest_asyncio.fixture
async def client(async_engine):
    from app.main import create_app

    app = create_app()
    app.dependency_overrides.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
