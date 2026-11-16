# fix/log-detected-positions

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Apply the smoothing study (plan Task 3 of `docs/plans/2026-11-16-tracker-gate.md`): log detected positions of confirmed markers, not smoothed ones.

## Steps
- 2026-11-16: `SMOOTHING = 1.0`; tests now expect detected positions. fdcl vibration tracked err clean/mild/moderate/severe 5.6/7.5/15.0/32.9 → 0.0/0.5/1.7/2.8 px; tracked 99.5/98.4/54.1/0.1% and false IDs unchanged. `benchmark --track` 53.2/2.4 before and after.
- 2026-11-16: Docs: READMEs, tracking and vision READMEs, navigation design note, notebook intro, AGENTS.md shake baseline (tracked 54.1%), DECISIONS.

## Decisions
- Approved by the project lead: no smoothing in logged positions; any smoothing for steering goes in `navigation`.

## Verification
- `./scripts/check.sh` passes. Benchmark and vibration test as above. Nothing run on hardware.

## Next Steps
- Revisit with flight footage.
