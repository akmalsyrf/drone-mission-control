from __future__ import annotations

from app.domain.value_objects import FlightMode

_MAVSDK_MODE_MAP: dict[str, FlightMode] = {
    "UNKNOWN": FlightMode.UNKNOWN,
    "READY": FlightMode.HOLD,
    "TAKEOFF": FlightMode.TAKEOFF,
    "HOLD": FlightMode.HOLD,
    "MISSION": FlightMode.MISSION,
    "RETURN_TO_LAUNCH": FlightMode.RTL,
    "LAND": FlightMode.LAND,
    "OFFBOARD": FlightMode.OFFBOARD,
    "FOLLOW_ME": FlightMode.AUTO,
    "MANUAL": FlightMode.MANUAL,
    "ALTCTL": FlightMode.ALTCTL,
    "POSCTL": FlightMode.POSCTL,
    "ACRO": FlightMode.MANUAL,
    "STABILIZED": FlightMode.MANUAL,
    "RATTITUDE": FlightMode.MANUAL,
}


def map_mavsdk_flight_mode(raw: str) -> FlightMode:
    key = raw.upper().replace(" ", "_")
    return _MAVSDK_MODE_MAP.get(key, FlightMode.UNKNOWN)
