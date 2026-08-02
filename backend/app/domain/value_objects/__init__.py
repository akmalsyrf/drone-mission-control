"""Domain value objects — immutable building blocks with no infrastructure deps."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AdapterType(StrEnum):
    PX4 = "px4"
    GAZEBO = "gazebo"
    DJI_CLOUD = "dji_cloud"
    SIMULATED = "simulated"


class ConnectionStatus(StrEnum):
    REGISTERED = "registered"
    CONNECTING = "connecting"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class FlightMode(StrEnum):
    UNKNOWN = "UNKNOWN"
    MANUAL = "MANUAL"
    ALTCTL = "ALTCTL"
    POSCTL = "POSCTL"
    AUTO = "AUTO"
    OFFBOARD = "OFFBOARD"
    RTL = "RTL"
    LAND = "LAND"
    TAKEOFF = "TAKEOFF"
    HOLD = "HOLD"
    MISSION = "MISSION"


class MissionStatus(StrEnum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VehicleCommand(StrEnum):
    ARM = "arm"
    DISARM = "disarm"
    TAKEOFF = "takeoff"
    LAND = "land"
    RTL = "rtl"
    HOLD = "hold"


class GeoPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    latitude_deg: float
    longitude_deg: float
    absolute_altitude_m: float | None = None
    relative_altitude_m: float | None = None


class Battery(BaseModel):
    model_config = ConfigDict(frozen=True)

    remaining_percent: float | None = None
    voltage_v: float | None = None


class VelocityNed(BaseModel):
    model_config = ConfigDict(frozen=True)

    north_m_s: float = 0.0
    east_m_s: float = 0.0
    down_m_s: float = 0.0

    @property
    def groundspeed_m_s(self) -> float:
        return float((self.north_m_s**2 + self.east_m_s**2) ** 0.5)


class GpsFix(BaseModel):
    model_config = ConfigDict(frozen=True)

    position: GeoPoint | None = None
    num_satellites: int | None = None
    fix_type: int | None = None


class WaypointSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    sequence: int = Field(ge=0)
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    hold_seconds: float = 0.0
