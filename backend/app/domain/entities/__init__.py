"""Domain entities — identity + lifecycle state. No framework imports."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import (
    AdapterType,
    Battery,
    ConnectionStatus,
    FlightMode,
    GpsFix,
    MissionStatus,
    VelocityNed,
    WaypointSpec,
)


class TelemetrySnapshot(BaseModel):
    """Canonical telemetry used across the stack (sim or hardware)."""

    model_config = ConfigDict(frozen=True)

    drone_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    gps: GpsFix = Field(default_factory=GpsFix)
    battery: Battery = Field(default_factory=Battery)
    heading_deg: float | None = None
    altitude_m: float | None = None
    relative_altitude_m: float | None = None
    flight_mode: FlightMode = FlightMode.UNKNOWN
    armed: bool = False
    speed_m_s: float | None = None
    velocity: VelocityNed | None = None
    source: AdapterType = AdapterType.PX4
    extras: dict[str, Any] = Field(default_factory=dict)


class Drone(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    adapter_type: AdapterType
    connection_uri: str
    connection_status: ConnectionStatus = ConnectionStatus.REGISTERED
    last_heartbeat: datetime | None = None
    current_mission_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Mission(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    drone_id: UUID
    name: str
    status: MissionStatus = MissionStatus.DRAFT
    waypoints: list[WaypointSpec] = Field(default_factory=list)
    progress_percent: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
