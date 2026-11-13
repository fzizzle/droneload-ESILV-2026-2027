# feature/camera-calibration

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
A checkerboard calibration command that writes the file `pose.py` reads (plan: `docs/plans/2026-11-13-camera-calibration.md`).

## Steps
- 2026-11-13: Added `calibrate.py` and `python -m droneload.vision.calibrate`, tested on rendered boards: focal length within 2%, a marker at 1.5 m within 3%.
- 2026-11-13: Review fixes: frames kept by board movement, not frame count (photo folders now work); warning when board tilt varies under 20°, since parallel views gave fx 8% wrong at RMS 0.28 px.

## Decisions
- `camera.yaml` is gitignored until the team decides where camera files live. Tilt is checked directly, because fx's standard deviation proved unreliable.

## Verification
- `./scripts/check.sh` passes. Webcam opened with no board, so no real calibration. Not tested on the drone's cameras or with a printed board.

## Next Steps
- Calibrate each camera once bought; decide where files are kept; deferred minors are in the PR.
