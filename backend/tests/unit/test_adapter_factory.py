from uuid import uuid4

import pytest

from app.config.settings import Settings
from app.domain.entities import Drone
from app.domain.value_objects import AdapterType
from app.drone.adapters.dji.dji_cloud_adapter import DjiCloudAdapter
from app.drone.adapters.gazebo.gazebo_adapter import GazeboSitlAdapter
from app.drone.adapters.mavsdk.px4_adapter import Px4MavsdkAdapter
from app.drone.adapters.simulated.simulated_adapter import SimulatedVehicleAdapter
from app.drone.factory import create_vehicle_adapter


def test_factory_routes_adapters() -> None:
    settings = Settings(app_env="test")
    cases = [
        (AdapterType.SIMULATED, "simulated://local", SimulatedVehicleAdapter),
        (AdapterType.PX4, "udpin://0.0.0.0:14550", Px4MavsdkAdapter),
        (AdapterType.GAZEBO, "udpin://0.0.0.0:14550", GazeboSitlAdapter),
        (AdapterType.DJI_CLOUD, "SN1", DjiCloudAdapter),
    ]
    for adapter_type, uri, expected in cases:
        drone = Drone(
            id=uuid4(),
            name=adapter_type.value,
            adapter_type=adapter_type,
            connection_uri=uri,
        )
        assert isinstance(create_vehicle_adapter(drone, settings), expected)


@pytest.mark.asyncio
async def test_dji_raises() -> None:
    with pytest.raises(NotImplementedError):
        await DjiCloudAdapter(uuid4(), "SN").connect()
