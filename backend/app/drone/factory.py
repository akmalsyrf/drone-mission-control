"""Vehicle adapter factory — Open/Closed selection by AdapterType."""

from __future__ import annotations

from app.config.settings import Settings
from app.domain.entities import Drone
from app.domain.interfaces import VehiclePort
from app.domain.value_objects import AdapterType
from app.drone.adapters.dji.dji_cloud_adapter import DjiCloudAdapter
from app.drone.adapters.gazebo.gazebo_adapter import GazeboSitlAdapter
from app.drone.adapters.mavsdk.px4_adapter import Px4MavsdkAdapter
from app.drone.adapters.simulated.simulated_adapter import SimulatedVehicleAdapter


def create_vehicle_adapter(drone: Drone, settings: Settings) -> VehiclePort:
    match drone.adapter_type:
        case AdapterType.PX4:
            return Px4MavsdkAdapter(
                drone.id,
                drone.connection_uri,
                publish_hz=settings.telemetry_publish_hz,
            )
        case AdapterType.GAZEBO:
            return GazeboSitlAdapter(
                drone.id,
                drone.connection_uri,
                publish_hz=settings.telemetry_publish_hz,
            )
        case AdapterType.SIMULATED:
            return SimulatedVehicleAdapter(
                drone.id,
                publish_hz=settings.telemetry_publish_hz,
            )
        case AdapterType.DJI_CLOUD:
            sn = str(drone.metadata.get("device_sn", drone.connection_uri))
            return DjiCloudAdapter(drone.id, sn)
        case _:
            raise ValueError(f"Unknown adapter type: {drone.adapter_type}")
