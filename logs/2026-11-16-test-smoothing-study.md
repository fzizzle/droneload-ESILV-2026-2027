# test/smoothing-study

**Agent:** Claude Code, Claude Opus 5.5
**Status:** in progress

## Goal
Study how the tracker's `SMOOTHING` weight affects position error and jitter on shaken footage, with Plotly charts and a notebook for the project report. Informs plan Task 3.

## Steps
- 2026-11-16: Design approved; plan in `docs/plans/2026-11-16-smoothing-study.md`.
- 2026-11-16: `MarkerTracker(smoothing=)` and a shake `seed`. fdcl vibration baseline unchanged: moderate raw 63.8% tracked 54.1%, err 3.7/15.0 px.
- 2026-11-16: `study.py` cross-check, fdcl seed 1 moderate: tracked 54.1% at every weight; frame err raw/0.6/1.0 3.7/15.0/1.7 px, matching the baseline. Steady err 36.9 px at 0.6, 40.9 at 1.0: smoothing cannot remove slow sway.

## Decisions
- Plotly, a rerunnable notebook, and deps in `analysis/requirements.txt` only (project lead).

## Verification
- Not run yet.

## Next Steps
- Build Tasks 1-5 of the plan.
