#!/usr/bin/env bash
# Build + run PX4 SITL Gazebo (gz_x500) on macOS Apple Silicon.
# Run from anywhere. Requires Homebrew Gazebo Harmonic + XQuartz.
set -euo pipefail

PX4_DIR="${PX4_DIR:-$HOME/robotics/PX4-Autopilot}"
export PATH="/opt/homebrew/bin:$PATH"
export CMAKE_PREFIX_PATH="/opt/homebrew/opt/opencv@4:$(brew --prefix qt@5 2>/dev/null || true)"
export OpenCV_DIR="/opt/homebrew/opt/opencv@4/lib/cmake/opencv4"

if [[ ! -d "$PX4_DIR" ]]; then
  echo "PX4 not found at $PX4_DIR"
  exit 1
fi

if ! command -v gz >/dev/null; then
  echo "gz not found. Install: brew install osrf/simulation/gz-harmonic"
  exit 1
fi

if [[ ! -d /Applications/Utilities/XQuartz.app && ! -d /opt/X11 ]]; then
  echo "XQuartz missing (needed for Gazebo GUI)."
  echo "Run in your own Terminal (needs password):"
  echo "  brew install --cask xquartz"
  echo "Then log out/in once."
  exit 1
fi

if [[ ! -d /opt/homebrew/opt/opencv@4 ]]; then
  echo "opencv@4 missing. Install: brew install opencv@4"
  exit 1
fi

cd "$PX4_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Using OpenCV: $OpenCV_DIR"
echo "Cleaning previous SITL build cache (forces OpenCV4 detect)…"
rm -rf build/px4_sitl_default

echo "Building + launching: make px4_sitl gz_x500"
echo "Leave this running. MAVLink should appear on UDP 14540."
exec make px4_sitl gz_x500
