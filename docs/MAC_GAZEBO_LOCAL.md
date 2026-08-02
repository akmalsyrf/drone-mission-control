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
| DMC `.env` | Already set to `gazebo` + `udp://127.0.0.1:14540` |

## A. Finish on your Mac (interactive)

### 1) XQuartz (GUI)

In **Terminal.app** (password required):

```bash
brew install --cask xquartz
```

Then **log out and log back in** once.

### 2) Launch PX4 + Gazebo GUI

```bash
cd ~/Documents/coding/studycase/drone-mission-control
./scripts/run-px4-gazebo-mac.sh
```

This cleans the SITL build cache, forces **OpenCV 4**, builds, and starts `gz_x500`.  
Leave it running. Expect XQuartz/Gazebo window + MAVLink on **UDP 14540**.

Manual equivalent:

```bash
cd ~/robotics/PX4-Autopilot
source .venv/bin/activate
export CMAKE_PREFIX_PATH="/opt/homebrew/opt/opencv@4:$(brew --prefix qt@5)"
export OpenCV_DIR="/opt/homebrew/opt/opencv@4/lib/cmake/opencv4"
rm -rf build/px4_sitl_default
make px4_sitl gz_x500
```

### 3) Connect DroneMissionControl

Already prepared via `./scripts/connect-local-gazebo.sh`:

```bash
APP_ENV=simulation
DRONE_DEFAULT_ADAPTER=gazebo
MAVSDK_SIM_ADDRESS=udp://127.0.0.1:14540
```

Run **API on the host** (not Docker) so UDP to localhost works:

```bash
cd ~/Documents/coding/studycase/drone-mission-control
docker compose up -d postgres redis mosquitto
# if an old sim-alpha drone is still in DB:
# docker compose down -v && docker compose up -d postgres redis mosquitto
make backend
make frontend
```

Open http://localhost:5173 — drone should be `gazebo` / live telemetry from SITL (not the spinning simulated circle).

Or register:

```bash
curl -X POST http://localhost:8000/api/v1/drones \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "gazebo-x500",
    "adapter_type": "gazebo",
    "connection_uri": "udp://127.0.0.1:14540",
    "auto_connect": true
  }'
```

## B. Why some steps need you

- **XQuartz installer** requires `sudo` / GUI password — agents cannot enter that.
- **Clean rebuild** of PX4 takes a long time on first `gz_x500`; script does it with the correct OpenCV4 path (OpenCV 5 breaks PX4 optical-flow C headers).

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| Build still sees OpenCV 5 | `rm -rf ~/robotics/PX4-Autopilot/build/px4_sitl_default` then rerun script |
| `types_c.h` not found | Ensure `opencv@4` and env vars above (do not point at OpenCV 5) |
| No GUI | Install XQuartz + re-login; open XQuartz once |
| DMC still circles | Old `simulated` drone — wipe DB volume or delete drone via API |
| NuttX submodule clone fails | Ignore for SITL; retry with `git -c http.version=HTTP/1.1 submodule update --init …` if needed later |

## References

- [PX4 macOS Development Environment](https://docs.px4.io/main/en/dev_setup/dev_env_mac.html)
- Helper scripts in this repo: `scripts/run-px4-gazebo-mac.sh`, `scripts/connect-local-gazebo.sh`
