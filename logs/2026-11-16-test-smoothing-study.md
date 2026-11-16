# test/smoothing-study

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Study how the tracker's `SMOOTHING` weight affects position error and jitter on shaken footage, with Plotly charts and a notebook for the project report. Informs plan Task 3.

## Steps
- 2026-11-16: Plan in `docs/plans/2026-11-16-smoothing-study.md`. Added `MarkerTracker(smoothing=)` and a shake `seed`; fdcl baseline unchanged (moderate raw 63.8%, tracked 54.1%, err 3.7/15.0 px). The study reproduces it at seed 1. Fixed the truth for duplicate IDs (42 fdcl, 19 Shadow frames). Means of seeds 1-3, moderate, w 0.6/1.0: fdcl frame err 15.2/1.7, steady 38.1/42.6, jitter 23.4/39.4 (true 39.3); Shadow frame err 6.3/1.4, steady 16.6/19.2, jitter 10.0/19.1 (true 22.0). Tracked is the same at every w.
- 2026-11-16: The final review found that the conclusion generalised the steady error from fdcl, whose camera moves. Corrected it: on a still scene (Shadow), smoothing does lower steady error. Also added a no-browser test, offline HTML, and a truth line in the trace that follows the nearest copy.

## Decisions
- Plotly, a rerunnable notebook, and deps in `analysis/requirements.txt` only (project lead).

## Verification
- `./scripts/check.sh` passes. Notebook run end to end with `nbconvert --execute` (0 errors), committed with outputs cleared. Nothing run on hardware.

## Next Steps
- Project lead decides `SMOOTHING` (plan Task 3) from the notebook.
