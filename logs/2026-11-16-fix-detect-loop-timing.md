# fix/detect-loop-timing

**Agent:** Claude Code (Claude Haiku)
**Status:** in progress

## Goal
Fix the detection loop's timing: no per-frame sleep, video time for files, correct recording speed.

## Steps
- 2026-11-16: Removed the per-frame `time.sleep(0.01)` from `droneload/vision/detect.py` and added `test_loop_does_not_sleep_between_frames`. Wall time for the 150-frame test video: 2.07 s before, 0.52 and 0.54 s after (the review measured 2.1 s and 0.5 s).

## Decisions
- The 0.05 s sleep after a failed read stays, so a dead camera does not spin.

## Verification
- Test went red (`[0.01, 0.01, 0.01] == []`), then green. `./scripts/check.sh` passes.
- Not run: `testing.benchmark` and `testing.vibration_test` (no detection change).

## Next Steps
- Task 3 and the rest of the branch: video time for files, recording speed.
