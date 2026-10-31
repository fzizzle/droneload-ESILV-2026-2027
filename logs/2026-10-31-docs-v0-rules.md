# docs/v0-rules

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Replace the slide-based contest summary with the organisers' V0 rules.

## Steps
- 2026-10-31: Rewrote `docs/contest-rules.md` and updated module READMEs, `TODO.md` and both READMEs.
- 2026-10-31: Updated `ARUCO_LABELS` to IDs 0-9, as approved by the user.
- 2026-10-31: Read Junior points from the coloured tables, which text extraction misses.

## Verification
- Tables checked against rendered PDF pages. Automatic maxima recomputed: 190, 260, 220.
- `./scripts/check.sh` passed. Benchmark not run: labels do not affect detection.

## Next Steps
- Update docs and labels when a later version of the rules appears.
