# fix/detect-loop-timing
**Agent:** Claude Code (Claude Haiku)
**Status:** ready for review

## Goal
Fix the detection loop's timing: no per-frame sleep, video time for files, correct recording speed.

## Steps
- 2026-11-16: Removed the per-frame `time.sleep(0.01)` and added `test_loop_does_not_sleep_between_frames`. 150-frame test video: 2.07 s before (one run), 0.52 and 0.54 s after.
- 2026-11-16: Video files now stamp `timestamp_ms` as start time plus frame position (`source_fps`, `OpenCVCamera` reads the file fps); live cameras keep the wall clock.
- 2026-11-16: `--record` keeps a file's frame rate; a live camera is written at 30 fps in real time via `frames_due`.
- 2026-11-16: Final review: `OpenCVCamera` keeps its fps when a file reports NaN, infinite or non-positive; recording rule and two open problems noted.

## Decisions
- The 0.05 s sleep after a failed read stays, so a dead camera does not spin.

## Verification
- Test went red (`[0.01, 0.01, 0.01] == []`), then green. `./scripts/check.sh` passes.
- Unverified on hardware: loop speed and live recording speed on a live camera. The "before" time is one run.
