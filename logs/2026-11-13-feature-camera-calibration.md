# feature/camera-calibration

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
A checkerboard calibration command that writes the file `pose.py` reads (plan: `docs/plans/2026-11-13-camera-calibration.md`).

## Steps
- 2026-11-13: Added `calibrate.py` functions with 6 tests on rendered boards: focal length within 2%, RMS under 0.5 px.
- 2026-11-13: Added `python -m droneload.vision.calibrate` with 5 more tests, including a marker at 1.5 m measured within 3%.
- 2026-11-13: Webcam smoke test: camera opened, Ctrl+C handled, no board shown, so it exited with an error and wrote nothing. No real calibration was done.

## Decisions
- `camera.yaml` is gitignored until the team decides where camera files live.

## Verification
- `./scripts/check.sh` passes. Not tested on the drone's cameras or with a printed board.

## Next Steps
- Calibrate each camera once bought, and decide where the files are kept.
