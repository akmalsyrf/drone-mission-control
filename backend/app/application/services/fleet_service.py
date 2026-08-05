"""Drone fleet use cases — application layer only."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.services.vehicle_supervisor import VehicleSupervisor
from app.config.logging import get_logger
from app.config.settings import Settings
from app.domain.entities import Drone, TelemetrySnapshot
from app.domain.interfaces import DroneRepositoryPort, TelemetryCachePort
from app.domain.value_objects import AdapterType, ConnectionStatus, VehicleCommand

logger = get_logger(__name__)


class DroneAlreadyExistsError(Exception):
    pass


class DroneNotFoundError(Exception):
    pass


class FleetService:
    def __init__(
        self,
        repository: DroneRepositoryPort,
        supervisor: VehicleSupervisor,
        telemetry_cache: TelemetryCachePort,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._supervisor = supervisor
        self._telemetry_cache = telemetry_cache
        self._settings = settings

    async def list_drones(self) -> list[Drone]:
        drones = await self._repository.list_all()
        enriched: list[Drone] = []
        for drone in drones:
            hb = self._supervisor.last_heartbeat(drone.id)
            if hb is not None and hb != drone.last_heartbeat:
                enriched.append(drone.model_copy(update={"last_heartbeat": hb}))
            else:
                enriched.append(drone)
        return enriched

    async def get_drone(self, drone_id: UUID) -> Drone:
        drone = await self._repository.get(drone_id)
        if drone is None:
            raise DroneNotFoundError(str(drone_id))
        hb = self._supervisor.last_heartbeat(drone_id)
        if hb is not None:
            return drone.model_copy(update={"last_heartbeat": hb})
        return drone

    async def register_drone(
        self,
        *,
        name: str,
        adapter_type: AdapterType | None = None,
        connection_uri: str | None = None,
        metadata: dict[str, object] | None = None,
        auto_connect: bool = True,
    ) -> Drone:
        adapter = adapter_type or self._settings.drone_default_adapter
        uri = connection_uri or self._settings.default_connection_uri
        drone = Drone(
            id=uuid4(),
            name=name,
            adapter_type=adapter,
            connection_uri=uri,
            connection_status=ConnectionStatus.REGISTERED,
            metadata=metadata or {},
        )
        try:
            saved = await self._repository.add(drone)
        except Exception as exc:
            raise DroneAlreadyExistsError(name) from exc
        if auto_connect:
            return await self.connect_drone(saved.id)
        return saved

    async def connect_drone(self, drone_id: UUID) -> Drone:
        drone = await self.get_drone(drone_id)
        connecting = drone.model_copy(update={"connection_status": ConnectionStatus.CONNECTING})
        await self._repository.save(connecting)
        await self._supervisor.start_drone(connecting)
        # Stay CONNECTING until the supervisor receives the first telemetry sample.
        return connecting

    async def disconnect_drone(self, drone_id: UUID) -> Drone:
        drone = await self.get_drone(drone_id)
        await self._supervisor.stop_drone(drone_id)
        offline = drone.model_copy(update={"connection_status": ConnectionStatus.OFFLINE})
        return await self._repository.save(offline)

    async def delete_drone(self, drone_id: UUID) -> None:
        await self._supervisor.stop_drone(drone_id)
        await self._repository.delete(drone_id)

    async def send_command(
        self,
        drone_id: UUID,
        command: VehicleCommand,
        altitude_m: float | None = None,
    ) -> None:
        adapter = self._supervisor.get_adapter(drone_id)
        if adapter is None:
            raise DroneNotFoundError(f"No active adapter for {drone_id}")
        await adapter.execute(command, altitude_m)
        logger.info("command_sent", drone_id=str(drone_id), command=command.value)

    async def latest_telemetry(self, drone_id: UUID) -> TelemetrySnapshot | None:
        await self.get_drone(drone_id)
        return await self._telemetry_cache.get_latest(drone_id)

    def _prefer_gazebo(self) -> bool:
        return (
            self._settings.app_env == "simulation"
            and self._settings.drone_default_adapter == AdapterType.GAZEBO
        )

    async def _normalize_gazebo_uri(self, drone: Drone) -> Drone:
        """Rewrite legacy SITL URIs (udp://…:14540) to the current GCS listen address."""
        uri = drone.connection_uri
        wanted = self._settings.mavsdk_sim_address
        legacy = "14540" in uri or uri.startswith("udp://")
        if uri == wanted or not legacy:
            return drone
        updated = drone.model_copy(update={"connection_uri": wanted})
        logger.info(
            "gazebo_uri_normalized",
            drone_id=str(drone.id),
            from_uri=uri,
            to_uri=wanted,
        )
        return await self._repository.save(updated)

    async def bootstrap_default_vehicle(self) -> Drone | None:
        """Empty fleet: seed a demo vehicle based on APP_ENV profile."""
        existing = await self._repository.list_all()
        prefer_gazebo = self._prefer_gazebo()

        if existing:
            reconnectable = {
                ConnectionStatus.ONLINE,
                ConnectionStatus.REGISTERED,
                ConnectionStatus.CONNECTING,
                ConnectionStatus.ERROR,
            }
            for drone in existing:
                if prefer_gazebo and drone.adapter_type == AdapterType.SIMULATED:
                    # Don't compete with the real SITL stream / confuse the UI.
                    await self._supervisor.stop_drone(drone.id)
                    offline = drone.model_copy(update={"connection_status": ConnectionStatus.OFFLINE})
                    await self._repository.save(offline)
                    logger.info("simulated_skipped_for_gazebo", drone_id=str(drone.id), name=drone.name)
                    continue
                if prefer_gazebo and drone.adapter_type == AdapterType.GAZEBO:
                    drone = await self._normalize_gazebo_uri(drone)
                    # Auto-reconnect gazebo vehicles even if left offline after a previous stop.
                    reconnectable = reconnectable | {ConnectionStatus.OFFLINE}
                if drone.connection_status in reconnectable:
                    connecting = drone.model_copy(
                        update={"connection_status": ConnectionStatus.CONNECTING}
                    )
                    await self._repository.save(connecting)
                    await self._supervisor.start_drone(connecting)
            return None

        if self._settings.app_env == "production":
            return None

        # Without SITL running, default to in-process simulated demo vehicle.
        # Set DRONE_DEFAULT_ADAPTER=gazebo and APP_ENV=simulation when PX4+Gazebo is up.
        if prefer_gazebo:
            return await self.register_drone(
                name="gazebo-sitl-1",
                adapter_type=AdapterType.GAZEBO,
                connection_uri=self._settings.mavsdk_sim_address,
                auto_connect=True,
            )
        return await self.register_drone(
            name="sim-alpha",
            adapter_type=AdapterType.SIMULATED,
            connection_uri="simulated://local",
            auto_connect=True,
        )
