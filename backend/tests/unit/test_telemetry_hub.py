"""Unit tests for TelemetryHub."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.domain.entities import TelemetrySnapshot
from app.domain.value_objects import AdapterType
from app.telemetry.hub import TelemetryHub


@pytest.mark.asyncio
async def test_hub_delivers_to_subscriber() -> None:
    hub = TelemetryHub()
    drone_id = uuid4()
    sample = TelemetrySnapshot(drone_id=drone_id, source=AdapterType.SIMULATED, armed=True)

    async def collect() -> TelemetrySnapshot:
        async for item in hub.subscribe(drone_id):
            return item
        raise AssertionError("empty")

    task = asyncio.create_task(collect())
    await asyncio.sleep(0.01)
    await hub.publish(sample)
    received = await asyncio.wait_for(task, timeout=1.0)
    assert received.armed is True


@pytest.mark.asyncio
async def test_hub_calls_handlers() -> None:
    hub = TelemetryHub()
    seen: list[str] = []

    async def handler(t: TelemetrySnapshot) -> None:
        seen.append(str(t.drone_id))

    hub.add_handler(handler)
    drone_id = uuid4()
    await hub.publish(TelemetrySnapshot(drone_id=drone_id, source=AdapterType.SIMULATED))
    assert seen == [str(drone_id)]
