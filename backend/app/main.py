"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import drones, health, missions
from app.config.logging import configure_logging, get_logger
from app.config.settings import get_settings
from app.di.container import build_container, shutdown_container, startup_container
from app.infrastructure.websocket.routes import router as websocket_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = await build_container(settings)
        app.state.container = container
        await startup_container(container)
        logger.info(
            "app_started",
            env=settings.app_env,
            simulation=settings.is_simulation,
            default_adapter=settings.drone_default_adapter.value,
        )
        try:
            yield
        finally:
            await shutdown_container(container)
            logger.info("app_stopped")

    app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(drones.router, prefix=settings.api_prefix)
    app.include_router(missions.router, prefix=settings.api_prefix)
    app.include_router(websocket_router)
    return app


app = create_app()
