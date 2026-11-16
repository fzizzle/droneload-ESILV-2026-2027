# test/vibration-footage

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Measure detection on poorly stabilised footage by shaking real test footage in `testing/vibration_test.py`.

## Steps
- 2026-11-16: Added `--source` and `--dict` to `vibration_test.py`: four shake levels (sway, jitter, rotation, blur along each move, rolling wobble), compared with clean footage, raw and tracked. Ran on Shadow-ArUco `video_5` and fdcl-gwu; results are in `droneload/vision/README.md`. On fdcl-gwu at moderate shake, raw 64%, tracked 33%. Added `--write` and `--level` to save shaken footage; tables unchanged after. Saved shaken footage to `test_footage/shaken/` and set the shake baseline in `AGENTS.md`.

## Decisions
- Extended the existing vibration test instead of adding a script; it reuses `motion_blur` and `rolling_wobble`.
- Markers the tracker confirms in at least 10 clean frames count as real, to exclude one-off false IDs.

## Verification
- `./scripts/check.sh` passes. Synthetic tables are unchanged. The shake is simulated, not drone footage.

## Next Steps
- Tracker `MAX_JUMP_PX` drops shaken markers (TODO.md). Benchmark not run: detection code is unchanged.
