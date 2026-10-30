# chore/reorganise-modules

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Organise the repository by module, so work and agent reading stay within one area.

## Steps
- 2026-10-30: Moved code to `droneload/vision`, `testing`, `tests` and `scripts`, and removed `Detect Aruco Realtime/`.
- 2026-10-30: Found that the earlier merge had deleted local `detections.csv` and `aruco_debug.jpg`. Restored both from `5971864` into `test_footage/sample-run/`.
- 2026-10-30: Added `docs/architecture.md`, planned module folders with one-line READMEs, and updated paths in all docs.

## Verification
- `./scripts/check.sh` passed. Benchmark unchanged: found=56.4% unmatched=26.6%.
- Not tested: CI on GitHub, and the scripts on a board.

## Next Steps
- Branch stacks on `docs/agent-rules`: merge that first.
