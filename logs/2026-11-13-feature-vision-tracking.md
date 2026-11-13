# feature/vision-tracking

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
Confirm markers across frames and smooth positions, to cut wrong IDs (plan: `docs/plans/2026-11-13-vision-tracking.md`).

## Steps
- 2026-11-13: Added `MarkerTracker` in `vision/tracking/tracker.py`, benchmark `--track`, and tracking in the detection loop (`--no-track` turns it off).
- 2026-11-13: Benchmark before: found=56.4% unmatched=26.6%. First version: 53.2%/2.4%.
- 2026-11-13: Review fixes: far detections no longer replace a confirmed track; jumps are checked against the last raw position, per frame missed; short videos save the last frame's debug image. After: 53.2%/2.7%. 2 of 5 frames gave 55.1%/7.1%.

## Decisions
- 3 of 5 frames: lowest unmatched for 3.2 points of found. Smoothing 0.6 did not change scores.

## Verification
- `./scripts/check.sh` passes. Shadow-ArUco `video_5` only; no real camera or `DICT_4X4_50` footage.

## Next Steps
- Skip blurred frames and use drone motion, once real footage exists.
