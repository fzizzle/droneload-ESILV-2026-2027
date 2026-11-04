# feature/flight-sitl

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Start the `flight` module: fly a demo in the ArduPilot simulator, since most points need automatic flight.

## Steps
- 2026-11-04: Added `scripts/sim.sh` (prebuilt Copter 4.7.2 SITL, checksummed) and `droneload/flight/vehicle.py` (pymavlink).
- 2026-11-04: First run stopped with a false pilot takeover: GUIDED sent during boot is reset to STABILIZE. Now waits for the heartbeat to leave the boot state.
- 2026-11-04: Added unit tests with a fake flight controller, and an opt-in simulator test that also checks takeover, run in CI.

## Decisions
- pymavlink, approved by the project owner. Connections are refused unless they reach a local simulator.

## Verification
- `./scripts/check.sh` passed. Simulator test passed locally in 14 s. Not tested on a drone or a Pixhawk.

## Next Steps
- Indoor positioning in the simulator (optical flow, rangefinder), and a command watchdog. See `TODO.md`.
