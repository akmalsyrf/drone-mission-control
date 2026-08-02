"""Mission application service."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.services.fleet_service import DroneNotFoundError
from app.application.services.vehicle_supervisor import VehicleSupervisor
from app.domain.entities import Mission
from app.domain.interfaces import DroneRepositoryPort, MissionRepositoryPort
from app.domain.value_objects import MissionStatus, WaypointSpec


class MissionNotFoundError(Exception):
    pass


class MissionService:
    def __init__(
        self,
        missions: MissionRepositoryPort,
        drones: DroneRepositoryPort,
        supervisor: VehicleSupervisor,
    ) -> None:
        self._missions = missions
        self._drones = drones
        self._supervisor = supervisor

    async def create_mission(
        self,
        drone_id: UUID,
        name: str,
        waypoints: list[WaypointSpec],
    ) -> Mission:
        drone = await self._drones.get(drone_id)
        if drone is None:
            raise DroneNotFoundError(str(drone_id))
        mission = Mission(
            id=uuid4(),
            drone_id=drone_id,
            name=name,
            status=MissionStatus.DRAFT,
            waypoints=waypoints,
        )
        return await self._missions.add(mission)

    async def list_missions(self, drone_id: UUID) -> list[Mission]:
        if await self._drones.get(drone_id) is None:
            raise DroneNotFoundError(str(drone_id))
        return await self._missions.list_for_drone(drone_id)

    async def upload_and_start(self, mission_id: UUID) -> Mission:
        mission = await self._missions.get(mission_id)
        if mission is None:
            raise MissionNotFoundError(str(mission_id))
        adapter = self._supervisor.get_adapter(mission.drone_id)
        if adapter is None:
            raise DroneNotFoundError(f"No active adapter for {mission.drone_id}")
        await adapter.upload(mission.waypoints)
        uploaded = mission.model_copy(update={"status": MissionStatus.UPLOADED})
        await self._missions.save(uploaded)
        await adapter.start()
        running = uploaded.model_copy(update={"status": MissionStatus.RUNNING})
        saved = await self._missions.save(running)
        drone = await self._drones.get(mission.drone_id)
        if drone is not None:
            await self._drones.save(drone.model_copy(update={"current_mission_id": mission.id}))
        return saved
