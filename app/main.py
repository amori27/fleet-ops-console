import asyncio
import contextlib

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.api.ws import ws_router
from app.config import get_settings
from app.db.engine import async_engine
from app.services.pubsub import PubSub

logger = structlog.get_logger()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.pubsub = PubSub()

    worker_task: asyncio.Task | None = None

    if settings.redis_url:
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            from arq.worker import Worker
            from app.telemetry.dispatcher import dispatch_action

            redis_pool = await create_pool(
                RedisSettings.from_dsn(settings.redis_url)
            )
            app.state.redis_pool = redis_pool

            worker = Worker(
                functions=[dispatch_action],
                redis_settings=RedisSettings.from_dsn(settings.redis_url),
                ctx={"pubsub": app.state.pubsub},
                burst=False,
                poll_delay=0.5,
            )
            worker_task = asyncio.create_task(worker.async_run())
            logger.info("ARQ worker started", redis_url=settings.redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable, running without ARQ worker", error=str(exc))

    logger.info("fleet_api_started")

    yield

    if worker_task is not None:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

    if hasattr(app.state, "redis_pool"):
        await app.state.redis_pool.close()

    await async_engine.dispose()
    logger.info("fleet_api_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fleet Ops Console API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(router)
    app.include_router(ws_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
