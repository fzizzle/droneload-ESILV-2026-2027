#!/bin/bash
# sim.sh - Download and run the ArduPilot copter simulator (SITL). Linux x86_64 only.
# Usage: ./scripts/sim.sh [--download-only] [--speedup N]
# Then, in another terminal: python -m droneload.flight

set -e

VERSION="4.7.2"
BASE="https://firmware.ardupilot.org/Copter/stable-$VERSION/SITL_x86_64_linux_gnu"
PARAMS_URL="https://raw.githubusercontent.com/ArduPilot/ardupilot/Copter-$VERSION/Tools/autotest/default_params/copter.parm"
BIN_SHA256="caed35e4cb796ec06cac40b09566a18251771486b1cbac5e2bf16b7a5ed5045d"
PARAMS_SHA256="5e01345b45d1c6190b28bece5638bbdd4cf1cce35e05bbbf480ab24d2b51aa0e"
DIR="${XDG_CACHE_HOME:-$HOME/.cache}/droneload/sitl-$VERSION"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PARAMS="copter.parm,$REPO/droneload/flight/failsafe.parm"
PARAMS="$PARAMS,$REPO/droneload/flight/stabilisation/indoor.parm,$REPO/testing/sitl_sensors.parm"

download_only=0
speedup=1
while [ $# -gt 0 ]; do
    case $1 in
        --download-only) download_only=1 ;;
        --speedup) speedup=$2; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

if [ "$(uname -s)-$(uname -m)" != "Linux-x86_64" ]; then
    echo "The prebuilt simulator needs Linux x86_64 (on Windows, use WSL)."
    exit 1
fi

mkdir -p "$DIR"
cd "$DIR"

fetch() {
    url=$1 file=$2 sum=$3
    if ! echo "$sum  $file" | sha256sum --check --status 2>/dev/null; then
        echo "Downloading $file"
        curl -sfL -o "$file" "$url"
        echo "$sum  $file" | sha256sum --check --quiet
    fi
}

fetch "$BASE/arducopter" arducopter "$BIN_SHA256"
fetch "$PARAMS_URL" copter.parm "$PARAMS_SHA256"
chmod +x arducopter

[ "$download_only" -eq 1 ] && exit 0

echo "Simulator listening on tcp:127.0.0.1:5760. Ctrl+C stops it."
exec ./arducopter --model quad --speedup "$speedup" --defaults "$PARAMS" --wipe
