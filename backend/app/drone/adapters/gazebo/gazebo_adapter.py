"""Gazebo + PX4 SITL adapter.

Same MAVSDK stack as hardware; waits for SITL home/GPS and tags telemetry
as AdapterType.GAZEBO so ops UIs can label simulation clearly.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from app.domain.entities import TelemetrySnapshot
from app.domain.value_objects import AdapterType, VehicleCommand, WaypointSpec
from app.drone.adapters.mavsdk.session import MavsdkSession


class GazeboSitlAdapter:
    def __init__(
        self,
        drone_id: UUID,
        system_address: str,
        *,
        publish_hz: float = 5.0,
    ) -> None:
        self._session = MavsdkSession(
            drone_id,
            system_address,
            source=AdapterType.GAZEBO,
            publish_hz=publish_hz,
            # Soft wait: stream still starts on timeout so the UI is not stuck forever.
            wait_for_gps=True,
        )

    @property
    def drone_id(self) -> UUID:
        return self._session.drone_id

    async def connect(self) -> None:
        await self._session.connect()

    async def disconnect(self) -> None:
        await self._session.disconnect()

    async def is_connected(self) -> bool:
        return await self._session.is_connected()

    async def arm(self) -> None:
        await self._session.execute(VehicleCommand.ARM)

    async def disarm(self) -> None:
        await self._session.execute(VehicleCommand.DISARM)

    async def takeoff(self, altitude_m: float) -> None:
        await self._session.execute(VehicleCommand.TAKEOFF, altitude_m)

    async def land(self) -> None:
        await self._session.execute(VehicleCommand.LAND)

    async def rtl(self) -> None:
        await self._session.execute(VehicleCommand.RTL)

    async def hold(self) -> None:
        await self._session.execute(VehicleCommand.HOLD)

    async def execute(self, command: VehicleCommand, altitude_m: float | None = None) -> None:
        await self._session.execute(command, altitude_m)

    async def stream(self) -> AsyncIterator[TelemetrySnapshot]:
        async for sample in self._session.stream():
            yield sample

    async def upload(self, waypoints: list[WaypointSpec]) -> None:
        await self._session.upload_mission(waypoints)

    async def start(self) -> None:
        await self._session.start_mission()

    async def pause(self) -> None:
        await self._session.pause_mission()

    async def clear(self) -> None:
        await self._session.clear_mission()

    async def progress_percent(self) -> float:
        return await self._session.mission_progress_percent()
