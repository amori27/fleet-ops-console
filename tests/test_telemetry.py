import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.telemetry_repo import get_latest_telemetry, upsert_telemetry


class TestTelemetryUpsert:
    async def test_insert_new_telemetry(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        record = {
            "device_id": device.id,
            "recorded_at": datetime.now(timezone.utc),
            "battery_level": 85.5,
            "lat": 10.0,
            "lng": 20.0,
            "signal_strength": -70.0,
        }

        inserted = await upsert_telemetry(async_session, [record])
        assert inserted == 1

        latest = await get_latest_telemetry(async_session, device.id)
        assert latest is not None
        assert latest.battery_level == 85.5

    async def test_upsert_updates_existing_record(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        recorded_at = datetime.now(timezone.utc)

        record = {
            "device_id": device.id,
            "recorded_at": recorded_at,
            "battery_level": 50.0,
            "signal_strength": -80.0,
        }
        await upsert_telemetry(async_session, [record])

        record["battery_level"] = 75.0
        inserted = await upsert_telemetry(async_session, [record])
        assert inserted == 0

        latest = await get_latest_telemetry(async_session, device.id)
        assert latest is not None
        assert latest.battery_level == 75.0

    async def test_upsert_is_idempotent_with_same_data(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        recorded_at = datetime.now(timezone.utc)

        record = {
            "device_id": device.id,
            "recorded_at": recorded_at,
            "battery_level": 90.0,
        }

        count1 = await upsert_telemetry(async_session, [record])
        count2 = await upsert_telemetry(async_session, [record])

        assert count1 == 1
        assert count2 == 0

    async def test_bulk_upsert(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        device = await device_factory.create(async_session)
        now = datetime.now(timezone.utc)

        records = [
            {
                "device_id": device.id,
                "recorded_at": now,
                "battery_level": float(i * 10),
            }
            for i in range(10)
        ]

        inserted = await upsert_telemetry(async_session, records)
        assert inserted == 10

    async def test_empty_records_returns_zero(
        self, async_session: AsyncSession
    ) -> None:
        inserted = await upsert_telemetry(async_session, [])
        assert inserted == 0
