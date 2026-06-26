# Fleet Ops Console API

Mission-critical backend for satellite and vehicle fleet operations. Built with FastAPI, SQLAlchemy 2.0 async, PostgreSQL, and ARQ.

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Run migrations
pip install -e ".[dev]"
alembic upgrade head

# 3. Start the API
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | Health check |
| `GET` | `/fleet/devices` | JWT (viewer) | Keyset-paginated device list |
| `GET` | `/fleet/devices/{id}` | JWT (viewer) | Device detail + latest telemetry |
| `POST` | `/fleet/telemetry` | API Key | Batch telemetry ingestion |
| `POST` | `/fleet/devices/{id}/actions` | JWT (commander) | Idempotent command dispatch |
| `GET` | `/fleet/devices/{id}/actions` | JWT (viewer) | Paginated action history |
| `WS` | `/ws/fleet/updates` | JWT | Live telemetry + action stream |

## Testing

```bash
pytest -v --asyncio-mode=auto
```

## Architecture

- **Keyset pagination** — O(1) cursor-based pagination with JSON+Base64 cursors
- **UPSERT ingestion** — `ON CONFLICT (device_id, recorded_at)` for safe retry
- **Idempotent commands** — `idempotency_key` UNIQUE constraint for at-most-once delivery
- **ARQ worker** — Redis-backed background job dispatch survives server crashes
- **Pub/Sub WebSocket** — asyncio.Queue hub broadcasts telemetry and action state changes
- **Dual auth** — API key for devices, JWT + RBAC for ops console users
