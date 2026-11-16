# docs/review-fixes-plan

**Agent:** Claude Code (Claude Fable 5.2)
**Status:** ready for review

## Goal
Plan the fixes from a performance and bug review of the app, and record the findings that need hardware.

## Steps
- 2026-11-16: Profiled the loop on a PC (4 OpenCV threads). Detection takes about 4 ms; the loop's `sleep(0.01)` costs more (72 fps with it, 285 without). Found the benchmark skips `MIN_SIDE_PX` (`unmatched` is 10.9% with it, not 26.6%), and that `polygonalApproxAccuracyRate` 0.03 beats 0.05 on both baselines.
- 2026-11-16: Wrote `docs/plans/2026-11-16-review-fixes.md` (7 tasks, 4 branches) and added 5 `TODO.md` items.

## Decisions
- Project lead: video files are timed by run start plus video position; a dead camera is reopened every 2 s; the `flight` fix stays in `TODO.md`.

## Verification
- `./scripts/check.sh` passes. Docs only. Measurements came from throwaway scripts, not committed.

## Next Steps
- Review the plan, then run it branch by branch, starting with `fix/benchmark-size-filter`.
