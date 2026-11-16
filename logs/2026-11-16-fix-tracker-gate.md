# fix/tracker-gate

**Agent:** Claude Code, Claude Opus 5.5
**Status:** in progress

## Goal
Stop the tracker discarding shaken markers the detector still finds (report row 1), and measure smoothing lag (row 2).

## Steps
- 2026-11-16: Prototyped with throwaway scripts. Moderate shake on fdcl-gwu, tracked/false IDs per 100 frames: 40 px 32.6%/0.2, 80 px 53.5/2.4, 120 px 54.1/3.5, no gate 54.4/10.0, max(20, 0.75 × side) 54.1/0.1. Bench `--track` unmatched 2.7, 3.3, 4.0, 6.6, 2.4.
- 2026-11-16: KLT camera-motion compensation with the 40 px gate: 54.1/3.2, 5.7 ms per frame on a PC. Dropped for now.
- 2026-11-16: Wrote `docs/plans/2026-11-16-tracker-gate.md`.

## Decisions
- Size-scaled gate, not motion compensation: same recall, fewer false IDs, no cost.

## Verification
- Not started.

## Next Steps
- Tasks 1-2 of the plan. Task 3 (smoothing) needs the project lead's decision.
