# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-01

### Added

- Initial project scaffold
- FastAPI application with async SQLAlchemy 2.0
- Device management API (list, detail, actions)
- Batch telemetry ingestion with UPSERT
- Keyset (cursor-based) pagination
- Dual authentication: API key (devices) + JWT/RBAC (ops users)
- WebSocket pub/sub for live telemetry and action updates
- ARQ background worker for idempotent command dispatch
- PostgreSQL + Redis infrastructure via Docker Compose
- Alembic migrations
- Test suite with pytest-asyncio and testcontainers
