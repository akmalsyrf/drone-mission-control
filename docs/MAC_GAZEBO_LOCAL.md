# Local Gazebo (GUI) + PX4 SITL on macOS → DroneMissionControl

Status on this machine (partially automated):

| Component | Status |
|-----------|--------|
| PX4 clone `~/robotics/PX4-Autopilot` | Ready |
| PX4 Python `.venv` | Ready |
| Gazebo Harmonic (`gz` 8.x) | Installed |
| OpenCV 4 (`opencv@4`) | Installed (needed by PX4 optical-flow plugin) |
| XQuartz | **You must install** (needs sudo password) |
| `make px4_sitl gz_x500` | Pending clean rebuild with OpenCV4 |
| DMC `.env` | Already set to `gazebo` + `udpin://0.0.0.0:14550` |

## A. Finish on your Mac (interactive)

### 1) XQuartz (GUI)

In **Terminal.app** (password required):

```bash
brew install --cask xquartz
```

Then **log out and log back in** once.

### 2) Launch PX4 + Gazebo GUI

**Important on macOS:** always export `DISPLAY=:0`, `GZ_IP=127.0.0.1`, and
`DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`. Without these, PX4 often loops
on `Waiting for Gazebo world...` then times out.

```bash
# clear any stuck gz from a failed launch
pkill -f 'gz sim' || true

cd ~/Documents/coding/studycase/drone-mission-control
./scripts/run-px4-gazebo-mac.sh
```

Or manually:

```bash
export DISPLAY=:0
export GZ_IP=127.0.0.1
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
export CMAKE_PREFIX_PATH="/opt/homebrew/opt/opencv@4:$(brew --prefix qt@5)"
export OpenCV_DIR="/opt/homebrew/opt/opencv@4/lib/cmake/opencv4"

open -a XQuartz
sleep 1
xhost +localhost

cd ~/robotics/PX4-Autopilot
source .venv/bin/activate
make px4_sitl gz_x500
```

Expect logs: `Gazebo world is ready` (not endless Waiting…). GUI opens via XQuartz.
Leave it running. MAVLink GCS ≈ UDP **14550** (PX4 local **18570** → remote **14550**).

Dashboard map defaults to **Baylands / California** with **Esri satellite** imagery (closer to Gazebo outdoor look than street maps) and a 3D/SVG quad marker — still not the Gazebo 3D viewport itself.

### More realistic world (baylands / lawn / forest)

`default.sdf` is an empty gray plane. Use a richer world:

```bash
pkill -f 'gz sim' || true
export PX4_GZ_WORLD=baylands   # or: lawn | forest | windy
./scripts/run-px4-gazebo-mac.sh
```

Worlds live in `~/robotics/PX4-Autopilot/Tools/simulation/gz/worlds/`.  
`baylands` pulls terrain/water from [Gazebo Fuel](https://fuel.gazebosim.org) on first launch (needs network; can take a few minutes).

### 3) Connect DroneMissionControl

Already prepared via `./scripts/connect-local-gazebo.sh`:

```bash
APP_ENV=simulation
DRONE_DEFAULT_ADAPTER=gazebo
MAVSDK_SIM_ADDRESS=udpin://0.0.0.0:14550
```

Run **API on the host** (not Docker) so UDP to localhost works:

```bash
cd ~/Documents/coding/studycase/drone-mission-control
docker compose up -d postgres redis mosquitto
# optional: delete leftover simulated drone via UI/API if it keeps republishing
make backend
make frontend
```

Open http://localhost:5173 — select the gazebo vehicle. Live telemetry should show GPS
near the SITL home (baylands ≈ 37.41, -122.00). The center panel is a **map** (MapLibre),
not a copy of the Gazebo 3D viewport.

Or register:

```bash
curl -X POST http://localhost:8000/api/v1/drones \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "gazebo-x500",
    "adapter_type": "gazebo",
    "connection_uri": "udpin://0.0.0.0:14550",
    "auto_connect": true
  }'
```

## B. Why some steps need you

- **XQuartz installer** requires `sudo` / GUI password — agents cannot enter that.
- **Clean rebuild** of PX4 takes a long time on first `gz_x500`; script does it with the correct OpenCV4 path (OpenCV 5 breaks PX4 optical-flow C headers).

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `Waiting for Gazebo world` timeout | `export DISPLAY=:0 GZ_IP=127.0.0.1 DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`; `pkill -f 'gz sim'`; open XQuartz; relaunch |
| No GUI | Install XQuartz + re-login; open XQuartz once |
| Build still sees OpenCV 5 | `rm -rf ~/robotics/PX4-Autopilot/build/px4_sitl_default` then rebuild with `opencv@4` env |
| `types_c.h` not found | Use `opencv@4` env vars (not OpenCV 5) |
| DMC “Waiting for stream…” | Use `udpin://0.0.0.0:14550`; ensure API loaded repo-root `.env`; delete/offline `sim-alpha` |
| NuttX submodule clone fails | Ignore for SITL; retry with `git -c http.version=HTTP/1.1 submodule update --init …` if needed later |

## References

- [PX4 macOS Development Environment](https://docs.px4.io/main/en/dev_setup/dev_env_mac.html)
- Helper scripts in this repo: `scripts/run-px4-gazebo-mac.sh`, `scripts/connect-local-gazebo.sh`
