from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import AdapterType, ConnectionStatus, FlightMode, VehicleCommand


class DroneCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    adapter_type: AdapterType | None = None
    connection_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    auto_connect: bool = True


class DroneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    adapter_type: AdapterType
    connection_uri: str
    connection_status: ConnectionStatus
    last_heartbeat: datetime | None = None
    current_mission_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommandBody(BaseModel):
    command: VehicleCommand
    altitude_m: float | None = Field(default=None, ge=0.5, le=500.0)


class GpsPositionSchema(BaseModel):
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    absolute_altitude_m: float | None = None
    relative_altitude_m: float | None = None


class GpsSchema(BaseModel):
    position: GpsPositionSchema | None = None
    num_satellites: int | None = None
    fix_type: int | None = None


class BatterySchema(BaseModel):
    remaining_percent: float | None = None
    voltage_v: float | None = None


class TelemetryResponse(BaseModel):
    drone_id: UUID
    timestamp: datetime
    gps: GpsSchema
    battery: BatterySchema
    heading_deg: float | None = None
    altitude_m: float | None = None
    relative_altitude_m: float | None = None
    flight_mode: FlightMode
    armed: bool
    speed_m_s: float | None = None
    source: AdapterType


class WaypointBody(BaseModel):
    sequence: int = Field(ge=0)
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    hold_seconds: float = 0.0


class MissionCreateRequest(BaseModel):
    name: str
    waypoints: list[WaypointBody]


class MissionResponse(BaseModel):
    id: UUID
    drone_id: UUID
    name: str
    status: str
    progress_percent: float
    waypoints: list[WaypointBody]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    simulation: bool
