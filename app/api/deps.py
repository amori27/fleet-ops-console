from fastapi import Query

from app.config import get_settings

settings = get_settings()


def pagination_params(
    cursor: str | None = Query(None, description="Opaque cursor for keyset pagination"),
    limit: int = Query(
        default=50,
        ge=1,
        le=settings.device_list_max_limit,
        description="Items per page",
    ),
) -> tuple[str | None, int]:
    return cursor, limit
