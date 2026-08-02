from uuid import uuid4

import pytest

from app.domain.value_objects import FlightMode, VehicleCommand
from app.drone.adapters.mavsdk.flight_mode import map_mavsdk_flight_mode
from app.drone.adapters.simulated.simulated_adapter import SimulatedVehicleAdapter


def test_flight_mode_mapping() -> None:
    assert map_mavsdk_flight_mode("MISSION") == FlightMode.MISSION
    assert map_mavsdk_flight_mode("return_to_launch") == FlightMode.RTL
    assert map_mavsdk_flight_mode("NOPE") == FlightMode.UNKNOWN


@pytest.mark.asyncio
async def test_simulated_stream_and_commands() -> None:
    adapter = SimulatedVehicleAdapter(uuid4(), publish_hz=40.0)
    await adapter.connect()
    await adapter.execute(VehicleCommand.ARM)
    await adapter.execute(VehicleCommand.TAKEOFF, 12.0)
    sample = None
    async for item in adapter.stream():
        sample = item
        break
    await adapter.disconnect()
    assert sample is not None
    assert sample.gps.position is not None
    assert sample.armed is True
    assert sample.source.value == "simulated"
