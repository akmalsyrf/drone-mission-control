from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.services.fleet_service import FleetService
from app.application.services.mission_service import MissionService
from app.application.services.vehicle_supervisor import VehicleSupervisor
from app.config.settings import Settings
from app.infrastructure.database.repositories.drone_repository import DroneRepository
from app.infrastructure.database.repositories.mission_repository import MissionRepository
from app.infrastructure.database.session import Base, create_engine, create_session_factory
from app.infrastructure.mqtt.publisher import MqttTelemetryPublisher
from app.infrastructure.redis.telemetry_cache import (
    RedisTelemetryBroadcaster,
    RedisTelemetryCache,
)
from app.telemetry.hub import TelemetryHub


@dataclass
class AppContainer:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    redis: redis.Redis
    telemetry_hub: TelemetryHub
    telemetry_cache: RedisTelemetryCache
    mqtt_publisher: MqttTelemetryPublisher
    drone_repository: DroneRepository
    mission_repository: MissionRepository
    vehicle_supervisor: VehicleSupervisor
    fleet_service: FleetService
    mission_service: MissionService


async def build_container(settings: Settings) -> AppContainer:
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    redis_client = redis.from_url(str(settings.redis_url), decode_responses=False)

    hub = TelemetryHub()
    cache = RedisTelemetryCache(redis_client, settings)
    redis_broadcaster = RedisTelemetryBroadcaster(redis_client, settings)
    mqtt = MqttTelemetryPublisher(settings)

    hub.add_handler(cache.set_latest)
    hub.add_broadcaster(redis_broadcaster)
    hub.add_broadcaster(mqtt)

    drones = DroneRepository(session_factory)
    missions = MissionRepository(session_factory)
    supervisor = VehicleSupervisor(hub, settings, drones)
    fleet = FleetService(drones, supervisor, cache, settings)
    mission_service = MissionService(missions, drones, supervisor)

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        redis=redis_client,
        telemetry_hub=hub,
        telemetry_cache=cache,
        mqtt_publisher=mqtt,
        drone_repository=drones,
        mission_repository=missions,
        vehicle_supervisor=supervisor,
        fleet_service=fleet,
        mission_service=mission_service,
    )


async def startup_container(container: AppContainer) -> None:
    async with container.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await container.mqtt_publisher.connect()
    await container.fleet_service.bootstrap_default_vehicle()


async def shutdown_container(container: AppContainer) -> None:
    await container.vehicle_supervisor.stop_all()
    await container.mqtt_publisher.disconnect()
    await container.redis.aclose()
    await container.engine.dispose()
