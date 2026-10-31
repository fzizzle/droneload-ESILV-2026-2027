# feature/vibration-test

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Plan for camera vibration, which the organisers say is usually a big problem.

## Steps
- 2026-10-31: Added `testing/vibration_test.py`, which simulates motion blur and rolling-shutter wobble.
- 2026-10-31: Added camera requirements and results to the `vision` README, plus `TODO.md` items.

## Verification
- `./scripts/check.sh` passed, with a new test. Detection code is unchanged, so the benchmark was not run.
- Simulated on clean images only. Not tested on a real camera or in flight.

## Next Steps
- Measure on footage from a flying drone, and confirm the camera choice.
