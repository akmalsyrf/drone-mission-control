#!/usr/bin/env bash
# Build (if needed) + run PX4 SITL Gazebo (gz_x500) on macOS Apple Silicon.
set -euo pipefail

PX4_DIR="${PX4_DIR:-$HOME/robotics/PX4-Autopilot}"
export PATH="/opt/homebrew/bin:$PATH"
export CMAKE_PREFIX_PATH="/opt/homebrew/opt/opencv@4:$(brew --prefix qt@5 2>/dev/null || true)"
export OpenCV_DIR="/opt/homebrew/opt/opencv@4/lib/cmake/opencv4"

# Critical on macOS — without these, gz often hangs and PX4 times out on world wait.
export DISPLAY="${DISPLAY:-:0}"
export GZ_IP="${GZ_IP:-127.0.0.1}"
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"

# Visual world (default.sdf = empty gray plane). Options in Tools/simulation/gz/worlds/:
# baylands | lawn | forest | windy | walls | aruco | ...
export PX4_GZ_WORLD="${PX4_GZ_WORLD:-baylands}"

if [[ ! -d "$PX4_DIR" ]]; then
  echo "PX4 not found at $PX4_DIR"
  exit 1
fi

if ! command -v gz >/dev/null; then
  echo "gz not found. Install: brew install osrf/simulation/gz-harmonic"
  exit 1
fi

if [[ ! -d /Applications/Utilities/XQuartz.app && ! -d /opt/X11 ]]; then
  echo "XQuartz missing. In Terminal.app: brew install --cask xquartz && log out/in"
  exit 1
fi

if [[ ! -d /opt/homebrew/opt/opencv@4 ]]; then
  echo "opencv@4 missing. Install: brew install opencv@4"
  exit 1
fi

# Prefer native macOS Terminal/XQuartz over a stale Cursor DISPLAY
open -a XQuartz >/dev/null 2>&1 || true
sleep 1
xhost +localhost >/dev/null 2>&1 || true

# Clear leftover gz from a previous timeout (otherwise world discovery races)
pkill -f 'gz sim' >/dev/null 2>&1 || true
sleep 1

cd "$PX4_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate

if [[ ! -x build/px4_sitl_default/bin/px4 ]]; then
  echo "PX4 SITL binary missing — building (first time / after clean)…"
  rm -rf build/px4_sitl_default
  make px4_sitl
fi

echo "DISPLAY=$DISPLAY  GZ_IP=$GZ_IP  PX4_GZ_WORLD=$PX4_GZ_WORLD"
echo "Launching: make px4_sitl gz_x500  (first baylands run may download Fuel meshes)"
echo "Leave this running. MAVLink GCS ≈ UDP 14550 (MAVSDK: udpin://0.0.0.0:14550)"
exec make px4_sitl gz_x500
