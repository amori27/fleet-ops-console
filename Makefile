.PHONY: all install run migrate test lint docker-up docker-down docker-logs dev-test docker-migrate

all: install run

install:
	@echo "Installing dependencies..."
	pip install -e ".[dev]"

run:
	@echo "Starting API server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	@echo "Running migrations..."
	alembic upgrade head

docker-up:
	@echo "Starting infrastructure (PostgreSQL + Redis)..."
	docker compose up -d
	docker compose logs -f

 docker-down:
	@echo "Stopping infrastructure..."
	docker compose down
	docker-logs:
	@echo "Viewing logs..."
	docker compose logs -f --follow

dev-test:
	@echo "Running tests..."
	pytest -v --asyncio-mode=auto
	docker-migrate:
	@echo "Running migrations in Docker..."
	docker compose run --rm api alembic upgrade head

lint:
	@echo "Checking code quality..."
	pyright app/ tests/
