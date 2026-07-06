# Contributing to fleet-ops-console

Thank you for your interest in contributing to **fleet-ops-console**! We welcome contributions from everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project is governed by a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its terms.

## Getting Started

1. Fork the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/amori27/fleet-ops-console.git
   cd fleet-ops-console
   ```
3. Start infrastructure services:
   ```bash
   docker compose up -d
   ```
4. Install the project with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
5. Run migrations:
   ```bash
   alembic upgrade head
   ```
6. Copy `.env.example` to `.env` and adjust as needed.

## Development Workflow

### Branching

- Create a feature branch from `main`:
  ```bash
  git checkout -b feat/your-feature-name
  ```
- Use prefixes like `feat/`, `fix/`, `docs/`, `refactor/`, `chore/`.

### Code Style

- This project uses **pyright** for type checking.
- Run the linter before committing:
  ```bash
  make lint
  ```

### Commits

Use clear, descriptive commit messages. We follow conventional commit style:

```
feat: add telemetry filtering by device type
fix: resolve race condition in WebSocket broadcast
docs: update API endpoint table in README
```

## Project Structure

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
├── pyproject.toml    # Project metadata and dependencies
├── Dockerfile        # Production container image
├── docker-compose.yml# Local development infrastructure
└── Makefile          # Common development commands
```

## Testing

Run the test suite:

```bash
pytest -v --asyncio-mode=auto
```

Tests use `testcontainers` to spin up real PostgreSQL instances, so Docker must be running.

## Pull Request Guidelines

1. Ensure all tests pass and the linter produces no errors.
2. Update documentation if your changes affect the public API.
3. Add tests for new functionality.
4. Keep pull requests focused — one feature or fix per PR.
5. Rebase your branch onto the latest `main` before submitting.

## Reporting Issues

- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for bugs.
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) for feature ideas.
- Check existing issues to avoid duplicates.

Thank you for helping improve fleet-ops-console!
