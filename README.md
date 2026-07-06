[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![CI](https://github.com/amori27/fleet-ops-console/actions/workflows/ci.yml/badge.svg)](https://github.com/amori27/fleet-ops-console/actions/workflows/ci.yml)
[![code style](https://img.shields.io/badge/code_style-pyright-7951B2)](https://github.com/microsoft/pyright)

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

## Folder Structure

```
fleet-ops-console/
├── app/
│   ├── api/          # Route handlers, WebSocket, error handlers, dependencies
│   ├── auth/         # API key and JWT authentication modules
│   ├── db/           # Database engine and base model setup
│   ├── models/       # SQLAlchemy ORM models (device, telemetry, action)
│   ├── repositories/ # Data access layer
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Business logic (device, telemetry, action, pubsub)
│   ├── telemetry/    # Telemetry ingestion dispatcher
│   ├── config.py     # Application settings via pydantic-settings
│   └── main.py       # FastAPI app factory and lifecycle
├── alembic/          # Database migrations
├── tests/            # pytest test suite
├── docs/             # Documentation
├── .github/          # CI workflows, issue templates, PR template
├── pyproject.toml    # Project metadata and dependencies
├── Dockerfile        # Production container image
├── docker-compose.yml# Local development infrastructure
├── Makefile          # Common development commands
├── CONTRIBUTING.md   # Contribution guidelines
├── CHANGELOG.md      # Release history
├── SECURITY.md       # Security policy
└── CODE_OF_CONDUCT.md# Community standards
