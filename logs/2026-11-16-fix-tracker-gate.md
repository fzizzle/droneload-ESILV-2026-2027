# fix/tracker-gate

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Stop the tracker discarding shaken markers the detector still finds (report row 1), and measure smoothing lag (row 2).

## Steps
- 2026-11-16: Prototype, fdcl moderate tracked / false IDs per 100 frames / bench `--track` unmatched: 40 px 32.6/0.2/2.7, 80 px 53.5/2.4/3.3, 120 px 54.1/3.5/4.0, none 54.4/10.0/6.6, max(20, 0.75 × side) 54.1/0.1/2.4. KLT motion compensation + 40 px: 54.1/3.2/2.8, 5.7 ms per frame. Chose the size-scaled gate: same recall, no more false IDs, no cost.
- 2026-11-16: Size-scaled gate. Bench 56.4/26.6 unchanged; `--track` 53.2/2.7 → 53.2/2.4. Tracked before → after, fdcl mild/moderate/severe 97.3/32.6/0.0 → 98.4/54.1/0.1; Shadow-ArUco 73/53/6 → 73.2/53.8/8.8 (raw 78.1/61.0/18.6).
- 2026-11-16: Position error in the vibration test. fdcl tracked err clean/mild/moderate: 5.6/7.5/15.0 px at SMOOTHING 0.6, 0.0/0.5/1.7 px at 1.0.

## Verification
- `./scripts/check.sh` passes. Benchmark and both vibration runs as above. Nothing run on hardware.

## Next Steps
- Plan Task 3, `SMOOTHING = 1.0`, needs the project lead's decision.
