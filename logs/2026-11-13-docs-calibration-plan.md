# docs/calibration-plan

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
Plan a checkerboard calibration command that writes the file `pose.py` reads.

## Steps
- 2026-11-13: Wrote `docs/plans/2026-11-13-camera-calibration.md`: calibration functions, then the command, an end-to-end pose check and docs.

## Decisions
- Checkerboard rather than ChArUco, as the TODO asks. Tests render a board through a known camera, so no hardware is needed.
- Calibration files are not committed until the team decides where they live.

## Verification
- Docs only. `./scripts/check.sh` run before the PR.

## Next Steps
- Review the plan, then implement it on a `feature/` branch.
