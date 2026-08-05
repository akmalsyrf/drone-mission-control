# Drone Mission Control

Production-minded fleet GCS starter: **PX4 hardware** and **PX4 SITL + Gazebo** share one application layer. Switch with env + adapter type — not business-logic forks.

## Architecture

```text
Presentation (FastAPI / WS / React)
        ↓
Application (FleetService, MissionService, VehicleSupervisor)
        ↓
Domain (entities, value objects, ports)
        ↑
Infrastructure + Drone adapters
  (Postgres, Redis, MQTT, MAVSDK PX4, Gazebo SITL, DJI stub)
```

| Layer | Responsibility |
|-------|----------------|
| **Domain** | `Drone`, `Mission`, `TelemetrySnapshot`, ports (`DroneController`, `TelemetryProvider`, `MissionProvider`) |
| **Application** | Use cases; no MAVSDK/SQL |
| **Drone adapters** | `px4`, `gazebo`, `simulated`, `dji_cloud` — compose shared `MavsdkSession` |
| **Infrastructure** | DB/repos, Redis, MQTT, WebSocket |

**Why separate Gazebo vs PX4 adapters:** same MAVSDK stack; different connection lifecycle (SITL home/GPS wait, sim tagging). Application stays identical.

## Quick start

```bash
cp .env.example .env
make bootstrap   # creates backend/.venv + npm install
make up          # Docker Compose: postgres redis mosquitto api ui nginx
```

- UI: http://localhost  
- API docs: http://localhost/docs  

First boot seeds **`sim-alpha`** (in-process simulated vehicle) when the fleet DB is empty.

## Simulation (PX4 SITL + Gazebo)

- **macOS (GUI):** see [docs/MAC_GAZEBO_LOCAL.md](docs/MAC_GAZEBO_LOCAL.md)  
  Helper: `./scripts/connect-local-gazebo.sh`
- **General:** [docs/PX4_GAZEBO_SITL.md](docs/PX4_GAZEBO_SITL.md)

```bash
APP_ENV=simulation
DRONE_DEFAULT_ADAPTER=gazebo
MAVSDK_SIM_ADDRESS=udpin://0.0.0.0:14550   # host API listens for PX4 GCS
```

## Production (real PX4)

```bash
APP_ENV=production
DRONE_DEFAULT_ADAPTER=px4
MAVSDK_HW_ADDRESS=serial:///dev/ttyUSB0:921600
```

## Backend layout

```text
backend/app/
  domain/           entities, value_objects, interfaces
  application/      FleetService, MissionService, VehicleSupervisor
  infrastructure/   database, redis, mqtt, websocket
  drone/adapters/   mavsdk/px4, gazebo, dji, simulated
  api/              thin HTTP controllers
  telemetry/        TelemetryHub
  auth/ config/ di/
```

## API (selected)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Liveness + env/simulation flags |
| GET/POST | `/api/v1/drones` | Fleet list / register |
| POST | `/api/v1/drones/{id}/commands` | arm…land |
| POST | `/api/v1/drones/{id}/missions` | Create waypoint mission |
| POST | `/api/v1/drones/{id}/missions/{mid}/start` | Upload + start on vehicle |
| WS | `/ws/telemetry?drone_id=*` | Live `TelemetrySnapshot` JSON |

## Tests & quality

```bash
make test
make lint
make typecheck
```

## Migrations

```bash
cd backend && .venv/bin/alembic upgrade head
```

On first Docker boot, SQLAlchemy `create_all` also creates tables (starter convenience). Prefer Alembic in shared environments.

## Extending to DJI Cloud

Implement `DjiCloudAdapter` against the Cloud API; map into the same ports + `TelemetrySnapshot`. Register with `adapter_type: "dji_cloud"`.
