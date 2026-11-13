# docs/vision-tracking-plan

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
List the work that can be done before hardware arrives, and plan the first tracking step.

## Steps
- 2026-11-13: Added "Can be built before hardware" to `TODO.md`.
- 2026-11-13: Wrote `docs/plans/2026-11-13-vision-tracking.md`: tracker, benchmark `--track`, detection loop `--no-track`.

## Decisions
- Plan covers confirm-across-frames and smoothing only; poor-frame skipping and motion correction wait for real footage.

## Verification
- Docs only. `./scripts/check.sh` run before the PR.

## Next Steps
- Review the plan, then implement it on a `feature/` branch.
