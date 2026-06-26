from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fleet"
    redis_url: str = "redis://localhost:6379"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    telemetry_batch_limit: int = 500
    device_list_default_limit: int = 50
    device_list_max_limit: int = 200

    model_config = {"env_prefix": "FLEET_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
