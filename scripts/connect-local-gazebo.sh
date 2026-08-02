#!/usr/bin/env bash
# Connect DroneMissionControl to a local PX4 Gazebo SITL on macOS.
#
# Prerequisites (one-time):
#   cd ~/robotics/PX4-Autopilot
#   ./Tools/setup/macos.sh --sim-tools
#   # log out/in if XQuartz was freshly installed
#   source .venv/bin/activate   # created by macos.sh
#   make px4_sitl gz_x500
#
# Then in another terminal, from the DMC repo:
#   ./scripts/connect-local-gazebo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Prefer host networking path when API runs on the Mac (make backend).
# Docker Desktop: use udp://host.docker.internal:14540 instead (see docs).
python3 - <<'PY'
from pathlib import Path
path = Path(".env")
text = path.read_text()
replacements = {
    "APP_ENV": "simulation",
    "DRONE_DEFAULT_ADAPTER": "gazebo",
    "MAVSDK_SIM_ADDRESS": "udp://127.0.0.1:14540",
}
lines = []
for line in text.splitlines():
    if not line or line.startswith("#") or "=" not in line:
        lines.append(line)
        continue
    key, _, _ = line.partition("=")
    if key in replacements:
        lines.append(f"{key}={replacements.pop(key)}")
    else:
        lines.append(line)
for key, value in replacements.items():
    lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n")
print("Updated .env for local Gazebo SITL:")
for k, v in {
    "APP_ENV": "simulation",
    "DRONE_DEFAULT_ADAPTER": "gazebo",
    "MAVSDK_SIM_ADDRESS": "udp://127.0.0.1:14540",
}.items():
    print(f"  {k}={v}")
PY

echo
echo "Next:"
echo "  1) Terminal A:  cd ~/robotics/PX4-Autopilot && source .venv/bin/activate && make px4_sitl gz_x500"
echo "  2) Terminal B:  docker compose up -d postgres redis mosquitto"
echo "  3) Terminal B:  make backend   # API on host so UDP to 127.0.0.1 works"
echo "  4) Terminal C:  make frontend"
echo "  5) UI: register/connect adapter_type=gazebo (or restart API to bootstrap gazebo-sitl-1)"
echo
echo "Dockerized backend instead of make backend:"
echo "  set MAVSDK_SIM_ADDRESS=udp://host.docker.internal:14540 in .env / compose"
