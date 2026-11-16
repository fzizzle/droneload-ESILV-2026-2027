# test/smoothing-study

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Study how the tracker's `SMOOTHING` weight affects position error and jitter on shaken footage, with Plotly charts and a notebook for the project report. Informs plan Task 3.

## Steps
- 2026-11-16: Plan in `docs/plans/2026-11-16-smoothing-study.md`. `MarkerTracker(smoothing=)` and a shake `seed`. fdcl vibration baseline unchanged: moderate raw 63.8% tracked 54.1%, err 3.7/15.0 px.
- 2026-11-16: `study.py` cross-check, fdcl seed 1 moderate: tracked 54.1% at every weight; frame err raw/0.6/1.0 3.7/15.0/1.7 px, matching the baseline. Steady err 36.9 px at 0.6, 40.9 at 1.0: smoothing cannot remove slow sway.
- 2026-11-16: Fixed duplicate IDs in the truth (42 fdcl, 19 Shadow frames); reports now match the nearest copy. Means of seeds 1-3, moderate, w 0.6/1.0: fdcl frame err 15.2/1.7, steady 38.1/42.6, jitter 23.4/39.4 (true 39.3); Shadow frame err 6.3/1.4, jitter 10.0/19.1 (true 22.0). Tracked unchanged by w.

## Decisions
- Plotly, a rerunnable notebook, and deps in `analysis/requirements.txt` only (project lead).

## Verification
- `./scripts/check.sh` passes. Notebook executed end to end with `nbconvert --execute`, 0 errors; committed with outputs cleared. Vibration baseline unchanged. Nothing run on hardware.

## Next Steps
- Project lead decides `SMOOTHING` (plan Task 3) from the notebook.
