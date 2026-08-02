from uuid import uuid4

from app.domain.entities import TelemetrySnapshot
from app.domain.value_objects import VelocityNed


def test_groundspeed() -> None:
    assert VelocityNed(north_m_s=3, east_m_s=4).groundspeed_m_s == 5.0


def test_telemetry_roundtrip() -> None:
    sample = TelemetrySnapshot(drone_id=uuid4(), armed=True, altitude_m=10.0)
    restored = TelemetrySnapshot.model_validate_json(sample.model_dump_json())
    assert restored.armed is True
    assert restored.altitude_m == 10.0
