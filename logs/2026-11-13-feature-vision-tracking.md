# feature/vision-tracking

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
Confirm markers across frames and smooth positions, to cut wrong IDs (plan: `docs/plans/2026-11-13-vision-tracking.md`).

## Steps
- 2026-11-13: Added `MarkerTracker` in `vision/tracking/tracker.py`, with 9 tests.
- 2026-11-13: Added `--track` to the benchmark. Before: found=56.4% unmatched=26.6%. After: found=53.2% unmatched=2.4%.
- 2026-11-13: Tuning: 2 of 5 frames gave 55.0%/6.1%; smoothing 0.6 or 1.0 made no difference.
- 2026-11-13: Detection loop uses the tracker by default; `--no-track` turns it off.

## Decisions
- 3 of 5 frames: lowest unmatched for 3.2 points of found. Smoothing kept at 0.6.

## Verification
- `./scripts/check.sh` passes. Benchmark on Shadow-ArUco `video_5` only; no real camera or `DICT_4X4_50` footage.

## Next Steps
- Skip blurred frames and use drone motion, once real footage exists.
