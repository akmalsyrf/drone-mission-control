"""Shared MAVSDK session — composed by PX4 and Gazebo adapters (no god inheritance)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.mission import MissionItem, MissionPlan

from app.config.logging import get_logger
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
from app.drone.adapters.mavsdk.flight_mode import map_mavsdk_flight_mode

logger = get_logger(__name__)


class MavsdkSession:
    """Low-level MAVSDK I/O used by hardware and SITL adapters via composition."""

    def __init__(
        self,
        drone_id: UUID,
        system_address: str,
        *,
        source: AdapterType,
        publish_hz: float = 5.0,
        wait_for_gps: bool = False,
    ) -> None:
        self._drone_id = drone_id
        self._system_address = system_address
        self._source = source
        self._interval = 1.0 / max(publish_hz, 0.1)
        self._wait_for_gps = wait_for_gps
        self._system = System()
        self._connected = False
        self._stop = asyncio.Event()
        self._gps = GpsFix()
        self._battery = Battery()
        self._heading_deg: float | None = None
        self._altitude_m: float | None = None
        self._relative_altitude_m: float | None = None
        self._flight_mode = FlightMode.UNKNOWN
        self._armed = False
        self._velocity = VelocityNed()
        self._tasks: list[asyncio.Task[None]] = []

    @property
    def drone_id(self) -> UUID:
        return self._drone_id

    async def connect(self) -> None:
        log = logger.bind(drone_id=str(self._drone_id), address=self._system_address)
        log.info("mavsdk_connecting", source=self._source.value)
        await self._system.connect(system_address=self._system_address)
        async for state in self._system.core.connection_state():
            if state.is_connected:
                self._connected = True
                log.info("mavsdk_connected")
                break
        if self._wait_for_gps:
            await self._await_home_position(timeout_s=20.0)
        self._stop.clear()
        self._tasks = [
            asyncio.create_task(self._collect_position()),
            asyncio.create_task(self._collect_battery()),
            asyncio.create_task(self._collect_heading()),
            asyncio.create_task(self._collect_flight_mode()),
            asyncio.create_task(self._collect_armed()),
            asyncio.create_task(self._collect_velocity()),
        ]

    async def disconnect(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()
        self._connected = False

    async def is_connected(self) -> bool:
        return self._connected

    async def stream(self) -> AsyncIterator[TelemetrySnapshot]:
        while not self._stop.is_set():
            yield TelemetrySnapshot(
                drone_id=self._drone_id,
                timestamp=datetime.now(UTC),
                gps=self._gps,
                battery=self._battery,
                heading_deg=self._heading_deg,
                altitude_m=self._altitude_m,
                relative_altitude_m=self._relative_altitude_m,
                flight_mode=self._flight_mode,
                armed=self._armed,
                speed_m_s=self._velocity.groundspeed_m_s,
                velocity=self._velocity,
                source=self._source,
            )
            await asyncio.sleep(self._interval)

    async def execute(self, command: VehicleCommand, altitude_m: float | None = None) -> None:
        if not self._connected:
            raise RuntimeError("Vehicle not connected")
        match command:
            case VehicleCommand.ARM:
                await self._system.action.arm()
            case VehicleCommand.DISARM:
                await self._system.action.disarm()
            case VehicleCommand.RTL:
                await self._system.action.return_to_launch()
            case VehicleCommand.HOLD:
                await self._system.action.hold()
            case VehicleCommand.LAND:
                await self._system.action.land()
            case VehicleCommand.TAKEOFF:
                alt = altitude_m if altitude_m is not None else 10.0
                await self._system.action.set_takeoff_altitude(alt)
                with suppress(ActionError):
                    await self._system.action.arm()
                await self._system.action.takeoff()
            case _:
                raise ValueError(f"Unsupported command: {command}")

    async def upload_mission(self, waypoints: list[WaypointSpec]) -> None:
        items = [
            MissionItem(
                wp.latitude_deg,
                wp.longitude_deg,
                wp.altitude_m,
                5.0,
                True,
                float("nan"),
                float("nan"),
                MissionItem.CameraAction.NONE,
                wp.hold_seconds,
                float("nan"),
                float("nan"),
                float("nan"),
                float("nan"),
                MissionItem.VehicleAction.NONE,
            )
            for wp in waypoints
        ]
        await self._system.mission.clear_mission()
        await self._system.mission.upload_mission(MissionPlan(items))

    async def start_mission(self) -> None:
        await self._system.mission.start_mission()

    async def pause_mission(self) -> None:
        await self._system.mission.pause_mission()

    async def clear_mission(self) -> None:
        await self._system.mission.clear_mission()

    async def mission_progress_percent(self) -> float:
        async for progress in self._system.mission.mission_progress():
            if progress.total == 0:
                return 0.0
            return 100.0 * float(progress.current) / float(progress.total)
        return 0.0

    async def _await_home_position(self, timeout_s: float) -> None:
        """SITL/Gazebo often needs a short wait before home/GPS is valid."""
        logger.info("waiting_for_sitl_home", drone_id=str(self._drone_id))
        try:
            async with asyncio.timeout(timeout_s):
                async for health in self._system.telemetry.health():
                    if health.is_home_position_ok or health.is_global_position_ok:
                        logger.info("sitl_home_ready", drone_id=str(self._drone_id))
                        return
        except TimeoutError:
            logger.warning("sitl_home_timeout", drone_id=str(self._drone_id))

    async def _collect_position(self) -> None:
        async for pos in self._system.telemetry.position():
            if self._stop.is_set():
                break
            point = GeoPoint(
                latitude_deg=pos.latitude_deg,
                longitude_deg=pos.longitude_deg,
                absolute_altitude_m=pos.absolute_altitude_m,
                relative_altitude_m=pos.relative_altitude_m,
            )
            self._gps = GpsFix(position=point)
            self._altitude_m = pos.absolute_altitude_m
            self._relative_altitude_m = pos.relative_altitude_m

    async def _collect_battery(self) -> None:
        async for battery in self._system.telemetry.battery():
            if self._stop.is_set():
                break
            pct = battery.remaining_percent
            if pct is not None and pct <= 1.0:
                pct = pct * 100.0
            self._battery = Battery(remaining_percent=pct, voltage_v=battery.voltage_v)

    async def _collect_heading(self) -> None:
        async for heading in self._system.telemetry.heading():
            if self._stop.is_set():
                break
            self._heading_deg = heading.heading_deg

    async def _collect_flight_mode(self) -> None:
        async for mode in self._system.telemetry.flight_mode():
            if self._stop.is_set():
                break
            self._flight_mode = map_mavsdk_flight_mode(str(mode))

    async def _collect_armed(self) -> None:
        async for armed in self._system.telemetry.armed():
            if self._stop.is_set():
                break
            self._armed = bool(armed)

    async def _collect_velocity(self) -> None:
        async for vel in self._system.telemetry.velocity_ned():
            if self._stop.is_set():
                break
            self._velocity = VelocityNed(
                north_m_s=vel.north_m_s,
                east_m_s=vel.east_m_s,
                down_m_s=vel.down_m_s,
            )
