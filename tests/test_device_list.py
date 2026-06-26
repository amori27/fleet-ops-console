import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.device_repo import _decode_cursor, list_devices


class TestKeysetPagination:
    async def test_paginates_through_all_devices(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create_batch(async_session, 105)

        all_ids: set = set()
        cursor: str | None = None
        page_count = 0

        while True:
            items, next_cursor = await list_devices(
                async_session, cursor=cursor, limit=50
            )
            page_count += 1
            assert len(items) <= 50
            for d in items:
                assert d.id not in all_ids, "Duplicate device across pages"
                all_ids.add(d.id)
            if next_cursor is None:
                break
            cursor = next_cursor

        assert page_count == 3
        assert len(all_ids) == 105

    async def test_respects_status_filter(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create_batch(async_session, 30, status="active")
        await device_factory.create_batch(async_session, 10, status="offline")

        items, _ = await list_devices(async_session, status="offline", limit=100)
        assert len(items) == 10

    async def test_empty_result(
        self, async_session: AsyncSession
    ) -> None:
        items, next_cursor = await list_devices(async_session, limit=50)
        assert len(items) == 0
        assert next_cursor is None

    async def test_cursor_is_opaque_json(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create(async_session)

        items, next_cursor = await list_devices(async_session, limit=1)
        assert next_cursor is not None

        decoded = _decode_cursor(next_cursor)
        assert "status" in decoded
        assert "last_seen" in decoded
        assert "id" in decoded

    async def test_respects_region_filter(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create_batch(async_session, 20, region="LEO")
        await device_factory.create_batch(async_session, 10, region="GEO")

        items, _ = await list_devices(async_session, region="GEO", limit=100)
        assert len(items) == 10


class TestDeviceSearch:
    async def test_full_text_search_finds_by_name(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create(async_session, name="target-satellite")
        await device_factory.create_batch(async_session, 30)

        items, _ = await list_devices(async_session, search="target", limit=100)
        assert len(items) == 1
        assert items[0].name == "target-satellite"

    async def test_search_returns_empty_for_non_matches(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create_batch(async_session, 30)

        items, _ = await list_devices(
            async_session, search="nonexistent-device", limit=100
        )
        assert len(items) == 0

    async def test_region_combined_with_search(
        self, async_session: AsyncSession, device_factory
    ) -> None:
        await device_factory.create(async_session, name="alpha-1", region="LEO")
        await device_factory.create(async_session, name="beta-1", region="GEO")

        items, _ = await list_devices(
            async_session, region="LEO", search="alpha", limit=100
        )
        assert len(items) == 1
