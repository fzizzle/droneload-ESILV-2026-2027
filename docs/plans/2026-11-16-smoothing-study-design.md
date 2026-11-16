# Smoothing Study: Design

**Status:** awaiting the project lead's approval.

## Why

Plan Task 3 (`docs/plans/2026-11-16-tracker-gate.md`) would set the tracker's `SMOOTHING` to 1.0, which turns smoothing off. Before deciding, the project lead wants a variable study of how the smoothing weight affects tracking on shaken footage. The charts and the notebook will go into the end-of-project report and be shown to teammates, so the steps must be repeatable and easy to follow.

## Goals

- Sweep `SMOOTHING` over 0.1, 0.2, …, 1.0 at every shake level (clean, mild, moderate, severe), on fdcl-gwu first and then Shadow-ArUco `video_5`.
- Measure, per weight and level:
  - **Frame error:** px from each reported position to the marker's true position in that shaken frame. This is the vibration test's `tracked err`, and the error that matters for logged pixel positions.
  - **Steady error:** px from each reported position to where the marker would be with the camera held still (the clean position under the zoom-only transform). Smoothing may lower this while raising frame error, and that is the trade-off the report should show.
  - **Jitter:** RMS frame-to-frame step of each reported position over consecutive frames, next to the same measure for the true position.
  - **Recall and false IDs**, as a check. The gate tests the last raw detection, so these should not change with the weight. A table confirms this.
- Plotly charts: frame error, steady error and jitter against the weight (one line per level); jitter against frame error (one point per weight); and a trace of one marker's x position over time at moderate shake (truth, raw, 0.6, 1.0).
- A notebook with numbered Markdown sections (question, method, measures, results, conclusion) and short code cells.

## Non-goals

- Choosing the weight. The study informs the lead's Task 3 decision; Task 3 is a separate change.
- New smoothers (1€, Kalman, offline smoothing). These are listed only as further work.
- Changing detection, the gate, the 3-of-5 rule or the CSV format.

## Anti-goals

- The study must use the same shake simulation as `testing/vibration_test.py`, or its numbers will not match the logged baseline.
- No generated output in git: no notebook outputs, charts or footage.

## Constraints

- New dependencies `plotly`, `kaleido`, `nbformat` and `jupyter` go in `analysis/requirements.txt` only (approved by the project lead on 2026-11-16). CI and the drone do not install them.
- PNG export through `kaleido` needs a Chromium-based browser (Chrome, Chromium, Edge, Brave or Vivaldi), or `plotly_get_chrome`.
- The footage is not in git. The notebook says how to fetch it (README "Test footage").
- `./scripts/check.sh` must pass. Ruff lints `.ipynb` files too.

## Approaches

1. **Module plus notebook (chosen).** `analysis/smoothing/study.py` holds the logic, and the notebook calls it. Detection runs once per footage, level and seed, and the cached detections are replayed through one tracker per weight. Smoothing does not change detection, so the sweep costs about one detection pass per level.
2. **Self-contained notebook.** Rejected: it would copy `vibration_test` logic that could drift, and leave nothing reusable outside Jupyter.
3. **Scripts only.** Rejected: teammates need to follow the steps.

## Decided

- Plotly for charts, not matplotlib (project lead).
- A structured `.ipynb` that teammates can rerun (project lead).
- Files: `analysis/smoothing/study.py`, `analysis/smoothing/smoothing_study.ipynb`, `analysis/requirements.txt`, `analysis/README.md`. Charts are exported to `analysis/smoothing/output/` as HTML and PNG, and that folder is gitignored.
- The notebook is committed with outputs cleared, because GitHub does not render Plotly output anyway.
- `MarkerTracker` gains `smoothing=SMOOTHING` in its constructor, with a test. The default behaviour is unchanged.
- The study imports `shaken_frames`, `find_markers`, `read_frames`, `map_point` and `SHAKE_LEVELS` from `testing/vibration_test.py`, and reuses its rule for real markers.

## Calls made by the agent (open to correction)

- Seeds 1, 2 and 3. Charts show the mean with a min-max band. Seed 1 alone reproduces the baseline. If runtime is too long, the seed list is a constant at the top of `study.py`.
- Shadow-ArUco uses `DICT_ARUCO_MIP_36h12` and fdcl-gwu uses `DICT_ARUCO_ORIGINAL`, as in the README.
- The trace chart uses the real marker with the most clean detections.
- Branch `test/smoothing-study`.

## Left to the builder

- How detections are cached (in memory or `.npz` in `output/`).
- Chart styling, provided each chart has a title, axis units and a legend.
- The steady transform: the clean position under `getRotationMatrix2D(centre, 0, zoom)`, with no shift. Verify this against `shake_frame`.
