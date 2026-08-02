"""In-process simulated vehicle for CI / demos without PX4 SITL."""

from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities import TelemetrySnapshot
from app.domain.value_objects import (
    AdapterType,
    Battery,
    FlightMode,
    GeoPoint,
    GpsFix,
    VehicleCommand,
    VelocityNed,
    WaypointSpec,
)


class SimulatedVehicleAdapter:
    def __init__(
        self,
        drone_id: UUID,
        *,
        home_lat: float = 47.397742,
        home_lon: float = 8.545594,
        publish_hz: float = 5.0,
    ) -> None:
        self._drone_id = drone_id
        self._home_lat = home_lat
        self._home_lon = home_lon
        self._interval = 1.0 / max(publish_hz, 0.1)
        self._connected = False
        self._stop = asyncio.Event()
        self._armed = False
        self._flight_mode = FlightMode.HOLD
        self._t = 0.0
        self._battery_pct = 100.0
        self._waypoints: list[WaypointSpec] = []
        self._mission_index = 0

    @property
    def drone_id(self) -> UUID:
        return self._drone_id

    async def connect(self) -> None:
        self._connected = True
        self._stop.clear()

    async def disconnect(self) -> None:
        self._stop.set()
        self._connected = False

    async def is_connected(self) -> bool:
        return self._connected

    async def arm(self) -> None:
        self._armed = True

    async def disarm(self) -> None:
        self._armed = False

    async def takeoff(self, altitude_m: float) -> None:
        self._armed = True
        self._flight_mode = FlightMode.TAKEOFF
        _ = altitude_m

    async def land(self) -> None:
        self._flight_mode = FlightMode.LAND

    async def rtl(self) -> None:
        self._flight_mode = FlightMode.RTL

    async def hold(self) -> None:
        self._flight_mode = FlightMode.HOLD

    async def execute(self, command: VehicleCommand, altitude_m: float | None = None) -> None:
        match command:
            case VehicleCommand.ARM:
                await self.arm()
            case VehicleCommand.DISARM:
                await self.disarm()
            case VehicleCommand.TAKEOFF:
                await self.takeoff(altitude_m or 10.0)
            case VehicleCommand.LAND:
                await self.land()
            case VehicleCommand.RTL:
                await self.rtl()
            case VehicleCommand.HOLD:
                await self.hold()

    async def stream(self) -> AsyncIterator[TelemetrySnapshot]:
        while not self._stop.is_set():
            radius = 0.0003
            lat = self._home_lat + radius * math.sin(self._t)
            lon = self._home_lon + radius * math.cos(self._t)
            heading = (math.degrees(self._t) + 90.0) % 360.0
            alt = 20.0 + 2.0 * math.sin(self._t / 2.0)
            speed = 3.5 + 0.5 * math.sin(self._t)
            self._battery_pct = max(5.0, self._battery_pct - 0.01)
            self._t += 0.05
            point = GeoPoint(
                latitude_deg=lat,
                longitude_deg=lon,
                absolute_altitude_m=alt + 400.0,
                relative_altitude_m=alt,
            )
            yield TelemetrySnapshot(
                drone_id=self._drone_id,
                timestamp=datetime.now(UTC),
                gps=GpsFix(position=point, num_satellites=14, fix_type=3),
                battery=Battery(remaining_percent=self._battery_pct, voltage_v=15.8),
                heading_deg=heading,
                altitude_m=alt + 400.0,
                relative_altitude_m=alt,
                flight_mode=self._flight_mode,
                armed=self._armed,
                speed_m_s=speed,
                velocity=VelocityNed(north_m_s=speed * 0.7, east_m_s=speed * 0.7),
                source=AdapterType.SIMULATED,
            )
            await asyncio.sleep(self._interval)

    async def upload(self, waypoints: list[WaypointSpec]) -> None:
        self._waypoints = list(waypoints)
        self._mission_index = 0

    async def start(self) -> None:
        self._flight_mode = FlightMode.MISSION
        self._armed = True

    async def pause(self) -> None:
        self._flight_mode = FlightMode.HOLD

    async def clear(self) -> None:
        self._waypoints = []
        self._mission_index = 0

    async def progress_percent(self) -> float:
        if not self._waypoints:
            return 0.0
        return 100.0 * float(self._mission_index) / float(len(self._waypoints))
