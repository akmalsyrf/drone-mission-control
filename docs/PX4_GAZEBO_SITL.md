# PX4 SITL + Gazebo with DroneMissionControl

This stack treats Gazebo/PX4 SITL as an external vehicle process.
DMC connects over MAVLink via MAVSDK — same application layer as hardware.

## Prerequisites

- PX4 Autopilot source (recommended) or prebuilt SITL
- Gazebo (Harmonic / Garden depending on PX4 version)
- MAVSDK-compatible MAVLink endpoint (default UDP 14540)

## Host setup (typical PX4 workflow)

```bash
# In PX4-Autopilot repo
make px4_sitl gazebo-classic_iris
# or newer: PX4_SYS_AUTOSTART=... px4
```

Confirm MAVLink is reachable:

```bash
# Common SITL GCS port
# udpin://0.0.0.0:14540
```

## Point DMC at SITL

```bash
# .env
APP_ENV=simulation
DRONE_DEFAULT_ADAPTER=gazebo
MAVSDK_SIM_ADDRESS=udpin://0.0.0.0:14540
```

Then register (or let bootstrap create `gazebo-sitl-1` when adapter=gazebo):

```bash
curl -X POST http://localhost:8000/api/v1/drones \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "gazebo-iris",
    "adapter_type": "gazebo",
    "connection_uri": "udpin://0.0.0.0:14540",
    "auto_connect": true
  }'
```

## Docker note

Full Gazebo-in-Compose needs GPU/display and a maintained PX4 image.
This starter keeps Gazebo on the host (or a dedicated sim box) and runs
API/DB/Redis/MQTT/UI in Compose — the usual robotics-lab pattern.

## Switching to real hardware

```bash
APP_ENV=production
DRONE_DEFAULT_ADAPTER=px4
MAVSDK_HW_ADDRESS=serial:///dev/ttyUSB0:921600
```

Register with `adapter_type: "px4"` and the radio/serial URI.
No application or frontend code changes required.
