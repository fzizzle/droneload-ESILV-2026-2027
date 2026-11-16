# fix/show-pacing

**Agent:** Claude Code (Claude Opus 5.5)
**Status:** ready for review

## Goal
Make `--show` play a video file at its own speed. Removing the per-frame sleep left only `waitKey(1)` to pace it.

## Steps
- 2026-11-16: Added `show_delay_ms()`; with `--show`, each frame of a file is held until the next one is due. Live cameras keep `waitKey(1)`.
- 2026-11-16: Tests failed first, then passed. The 5 s test video now plays in 5.03 s with `--show` (fake window that really waits); without `--show` it still takes 0.50 s.

## Decisions
- Pace only with `--show` and a file source, so detection runs and live cameras stay as fast as they are.

## Verification
- `./scripts/check.sh` passes. A real window was not opened (no display here). Benchmark not run: timing only, not detection.

## Next Steps
- None.
