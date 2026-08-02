"""Fleet vehicle supervisor — N adapter lifecycle tasks."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from app.config.logging import get_logger
from app.config.settings import Settings
from app.domain.entities import Drone
from app.domain.interfaces import VehiclePort
from app.drone.factory import create_vehicle_adapter
from app.telemetry.hub import TelemetryHub

logger = get_logger(__name__)


class VehicleSupervisor:
    def __init__(self, hub: TelemetryHub, settings: Settings) -> None:
        self._hub = hub
        self._settings = settings
        self._adapters: dict[UUID, VehiclePort] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._heartbeats: dict[UUID, datetime] = {}

    def get_adapter(self, drone_id: UUID) -> VehiclePort | None:
        return self._adapters.get(drone_id)

    def last_heartbeat(self, drone_id: UUID) -> datetime | None:
        return self._heartbeats.get(drone_id)

    async def start_drone(self, drone: Drone) -> None:
        async with self._lock:
            if drone.id in self._adapters:
                return
            adapter = create_vehicle_adapter(drone, self._settings)
            self._adapters[drone.id] = adapter
            self._tasks[drone.id] = asyncio.create_task(
                self._run_adapter(drone, adapter),
                name=f"vehicle-{drone.id}",
            )

    async def stop_drone(self, drone_id: UUID) -> None:
        async with self._lock:
            task = self._tasks.pop(drone_id, None)
            adapter = self._adapters.pop(drone_id, None)
            self._heartbeats.pop(drone_id, None)
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if adapter is not None:
            with suppress(Exception):
                await adapter.disconnect()

    async def stop_all(self) -> None:
        for drone_id in list(self._adapters.keys()):
            await self.stop_drone(drone_id)

    async def _run_adapter(self, drone: Drone, adapter: VehiclePort) -> None:
        log = logger.bind(drone_id=str(drone.id), name=drone.name, adapter=drone.adapter_type.value)
        try:
            await adapter.connect()
            log.info("vehicle_online")
            async for sample in adapter.stream():
                self._heartbeats[drone.id] = datetime.now(UTC)
                await self._hub.publish(sample)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("vehicle_adapter_failed")
        finally:
            with suppress(Exception):
                await adapter.disconnect()
            log.info("vehicle_offline")
