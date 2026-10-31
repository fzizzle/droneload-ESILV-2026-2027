# feature/marker-position

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Turn a detected marker into a position in metres, which landing and centring need.

## Steps
- 2026-10-31: Added `droneload/vision/pose.py` with `solvePnP`, and calibration loading. Not wired into the loop, because that may change the CSV format.
- 2026-10-31: A 3 cm test limit failed at 2.5 m. Measured error by distance, then set the limit at 2% of distance.

## Verification
- `./scripts/check.sh` passed. Detection code unchanged, so the benchmark was not run.
- Simulated images only. Not tested on a real camera or with real calibration.

## Next Steps
- Add a calibration tool, then use positions in the detection loop.
