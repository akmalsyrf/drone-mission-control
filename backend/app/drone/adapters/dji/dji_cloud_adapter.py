"""DJI Cloud API stub — keep the seam visible for future work."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from app.domain.entities import TelemetrySnapshot
from app.domain.value_objects import VehicleCommand, WaypointSpec


class DjiCloudAdapter:
    def __init__(self, drone_id: UUID, device_sn: str) -> None:
        self._drone_id = drone_id
        self._device_sn = device_sn

    @property
    def drone_id(self) -> UUID:
        return self._drone_id

    async def connect(self) -> None:
        raise NotImplementedError(f"DJI Cloud adapter not implemented (sn={self._device_sn})")

    async def disconnect(self) -> None:
        return None

    async def is_connected(self) -> bool:
        return False

    async def arm(self) -> None:
        raise NotImplementedError

    async def disarm(self) -> None:
        raise NotImplementedError

    async def takeoff(self, altitude_m: float) -> None:
        raise NotImplementedError

    async def land(self) -> None:
        raise NotImplementedError

    async def rtl(self) -> None:
        raise NotImplementedError

    async def hold(self) -> None:
        raise NotImplementedError

    async def execute(self, command: VehicleCommand, altitude_m: float | None = None) -> None:
        raise NotImplementedError(f"DJI command not implemented: {command}")

    async def stream(self) -> AsyncIterator[TelemetrySnapshot]:
        raise NotImplementedError
        yield  # pragma: no cover

    async def upload(self, waypoints: list[WaypointSpec]) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        raise NotImplementedError

    async def pause(self) -> None:
        raise NotImplementedError

    async def clear(self) -> None:
        raise NotImplementedError

    async def progress_percent(self) -> float:
        return 0.0
