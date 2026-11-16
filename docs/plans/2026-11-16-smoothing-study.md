# Smoothing Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure how the tracker's `SMOOTHING` weight changes position error and jitter on shaken footage, with Plotly charts and a rerunnable notebook for the project report.

**Architecture:** `analysis/smoothing/study.py` (numpy only) shakes footage with `testing/vibration_test.py`, detects once per level and seed, caches the detections, and replays them through one `MarkerTracker` per weight. `analysis/smoothing/charts.py` turns its summary into Plotly figures. `analysis/smoothing/smoothing_study.ipynb` walks through the steps.

**Tech Stack:** Python 3.12, OpenCV 4.10, numpy, Plotly, kaleido, nbformat, Jupyter.

**Spec:** `docs/plans/2026-11-16-smoothing-study-design.md`

## Global Constraints

- `plotly`, `kaleido`, `nbformat` and `jupyter` go in `analysis/requirements.txt` only. Leave `requirements-dev.txt` unchanged, because CI does not install them.
- Only `charts.py` and the notebook may import plotly. `study.py` and the tests must run without it.
- Weights are `0.1, 0.2, …, 1.0`. Seeds are `(1, 2, 3)`. Levels are `vibration_test.SHAKE_LEVELS`.
- Footage: fdcl-gwu `test_footage/fdcl-gwu/test_video.mp4` with `DICT_ARUCO_ORIGINAL`, and Shadow-ArUco `test_footage/shadow-aruco/video_5/%05d.png` with `DICT_ARUCO_MIP_36h12`.
- No generated output in git. `analysis/smoothing/output/` and `.ipynb_checkpoints/` are gitignored, and the notebook is committed with outputs cleared.
- Default behaviour of `MarkerTracker` and `vibration_test` must not change. `vibration_test --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL` must still print moderate `raw 63.8% tracked 54.1%`.
- Match the repo style: settings in constants at the top of the file, aligned assignments, and short comments.

## Review Focus

- The notebook runs from `analysis/smoothing/`, not the repo root. It must find the repo root itself (Task 5, setup cell).
- Footage is missing on a fresh clone. `load_or_detect` must raise `FileNotFoundError` that names the README section "Test Footage" (Task 3 test `test_missing_footage_names_readme`).
- No Chromium-based browser is installed. `save` must still write the HTML and print a warning instead of raising (Task 4 test `test_save_without_png_writes_html`).
- At severe shake a marker may never be reported, which leaves metrics empty. Metrics are `nan`, not an exception, and `summarise` ignores `nan` (Task 3 test `test_measure_no_reports_is_nan`).
- A stale cache after `SEEDS` changes. The cache file name includes the seeds (Task 3 test `test_cache_path_includes_seeds`).

---

### Task 1: Tracker smoothing weight as a parameter

**Files:**
- Modify: `droneload/vision/tracking/tracker.py` (`MarkerTracker.__init__`, `update`)
- Test: `tests/test_tracking.py`

**Interfaces:**
- Produces: `MarkerTracker(smoothing: float = SMOOTHING)`; `update` uses `self.smoothing` instead of the module constant.

- [ ] **Step 1: Write the failing test** in `tests/test_tracking.py`:

```python
def test_smoothing_weight_is_configurable():
    tracker = MarkerTracker(smoothing=1.0)
    out = [tracker.update([(1, x, 0, SIDE)]) for x in (0, 0, 0, 10)]
    assert out[-1] == [(1, 10.0, 0.0)]
```

- [ ] **Step 2: Run** `python -m pytest tests/test_tracking.py -q`. Expected: the new test fails with `TypeError` (unexpected keyword `smoothing`).
- [ ] **Step 3: Implement.** Add `smoothing=SMOOTHING` to `__init__`, store it, and use it in the two smoothing lines.
- [ ] **Step 4: Run** `python -m pytest tests/test_tracking.py -q`. Expected: all pass, including the unchanged `test_smooths_position`.
- [ ] **Step 5: Commit** `tracker.py` and `tests/test_tracking.py`: "Let the tracker take its smoothing weight".

### Task 2: Seeded shake in the vibration test

**Files:**
- Modify: `testing/vibration_test.py` (`shake_path`, `shaken_frames`)
- Test: `tests/test_detect.py`

**Interfaces:**
- Produces: `shake_path(count, level, scale, seed=SEED)` and `shaken_frames(frames, level, seed=SEED)`. Every other call site keeps the default.

- [ ] **Step 1: Write the failing test** in `tests/test_detect.py`:

```python
def test_shake_path_seed():
    level = vibration_test.SHAKE_LEVELS["moderate"]
    default = vibration_test.shake_path(50, level, 1.0)
    assert (default == vibration_test.shake_path(50, level, 1.0, seed=vibration_test.SEED)).all()
    assert not (default == vibration_test.shake_path(50, level, 1.0, seed=2)).all()
```

- [ ] **Step 2: Run** `python -m pytest tests/test_detect.py -q -k seed`. Expected: FAIL with `TypeError`.
- [ ] **Step 3: Implement** the two parameters. `shaken_frames` passes `seed` on to `shake_path`.
- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`. Then run `python -m testing.vibration_test --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL`. Expected: moderate still shows `63.8%` raw and `54.1%` tracked. Log the result.
- [ ] **Step 5: Commit** `vibration_test.py` and `tests/test_detect.py`: "Let the vibration test take a shake seed".

### Task 3: Study data layer

**Files:**
- Create: `analysis/__init__.py`, `analysis/smoothing/__init__.py` (both empty), `analysis/smoothing/study.py`, `analysis/requirements.txt`
- Modify: `.gitignore` (add `analysis/smoothing/output/` and `.ipynb_checkpoints/`)
- Test: `tests/test_smoothing_study.py`

**Interfaces:**
- Consumes: `MarkerTracker(smoothing=...)` (Task 1); `vibration_test.shaken_frames(frames, level, seed)` (Task 2); `vibration_test.read_frames`, `find_markers`, `first_by_id`, `map_point`, `shake_run`, `SHAKE_LEVELS`, `REAL_MIN_FRAMES`.
- Produces:
  - Constants: `WEIGHTS = [0.1, …, 1.0]` (rounded to 1 decimal), `SEEDS = (1, 2, 3)`, `FOOTAGE = {"fdcl-gwu": (path, dict), "shadow-aruco": (path, dict)}`, `ROOT` (the repo root, `Path(__file__).resolve().parents[2]`), `OUTPUT_DIR = Path(__file__).parent / "output"`.
  - `@dataclass Run`: `level: str`, `seed: int`, `detections: list[list[tuple]]` (the `find_markers` output per frame), `truth: list[dict]` (`{id: (x, y)}` in the shaken frame), `steady: list[dict]` (`{id: (x, y)}` under the zoom-only transform).
  - `@dataclass Detected`: `footage: str`, `real: set[int]`, `reference: list[set[int]]` (real IDs the clean detector found per frame), `runs: list[Run]`.
  - `steady_matrix(width: int, height: int, zoom: float) -> np.ndarray` (2x3): `cv2.getRotationMatrix2D((width / 2, height / 2), 0, zoom)`.
  - `detect_runs(frames, dict_name, seeds=SEEDS, footage="") -> Detected`. Find the clean positions and `real` exactly as `vibration_test.shake_rates` does, using `shake_run` at `clean`. Clean gets one `Run` with `seed=seeds[0]`, because shaking does not use the seed there. Every other level gets one `Run` per seed.
  - `cache_path(footage: str, seeds) -> Path`: `OUTPUT_DIR / f"{footage}-seeds-{'-'.join(map(str, seeds))}.pkl"`.
  - `load_or_detect(footage: str, seeds=SEEDS, refresh=False) -> Detected`: pickle cache. If the footage is missing, raise `FileNotFoundError` naming the path and the README section "Test Footage". Read the frames only when detecting, so about 5 GB of fdcl frames is freed after the call.
  - `replay(detections, smoothing: float | None) -> list[dict]`: `{id: (cx, cy)}` per frame from a fresh `MarkerTracker(smoothing)`, via `first_by_id`. `None` means the raw detections (`first_by_id` of each frame, no tracker).
  - `measure(run: Run, reported: list[dict], detected: Detected) -> dict` with keys `frame_err_px`, `steady_err_px`, `jitter_px`, `true_jitter_px`, `tracked`, `false_ids`. Errors are mean distances over (frame, ID) pairs present in both maps. `jitter_px` is the RMS step of reported positions between consecutive frames where the ID is reported in both. `true_jitter_px` is the same over `run.truth` on those same frame pairs. `tracked` and `false_ids` are defined as in `vibration_test.shake_rates` (share of `reference` reported; non-real IDs per 100 frames). An empty set gives `nan`.
  - `sweep(detected: Detected, weights=WEIGHTS) -> list[dict]`: one row per run and weight, plus `weight=None` for raw. Keys: `footage, level, seed, weight` plus the `measure` keys.
  - `summarise(rows) -> list[dict]`: one row per `(footage, level, weight)` with `{metric}_mean`, `{metric}_min` and `{metric}_max` for each measure, ignoring `nan`. Keep level order as in `SHAKE_LEVELS`, raw first, then weights ascending.
  - `busiest_marker(detected) -> int`: the real ID present in the most `reference` frames.
  - `trace(detected, level="moderate", seed=SEEDS[0], weights=(0.6, 1.0), marker_id=None) -> dict` with keys `marker_id`, `frames` (list of int), `truth_x`, `raw_x` and `weights` (`{w: [x or None]}`), each with `None` where not present.
  - `format_table(summary, metrics=("tracked", "false_ids")) -> str`: a plain text table, one line per level and weight, in the style of `vibration_test.print_shake_table`.

- [ ] **Step 1: Write failing tests** in `tests/test_smoothing_study.py`. Use synthetic detections `(id, x, y, 60)` and, for `detect_runs`, `[vibration_test.make_frame(240)] * 15` with `DICT_4X4_50`:
  - `test_replay_full_weight_reports_detections`: four frames of ID 1 at x = 0, 10, 20, 30. `replay(d, 1.0)[3] == {1: (30.0, 0.0)}`. At 0.5, frame 3 x < 30. `replay(d, None)[0] == {1: (0.0, 0.0)}`.
  - `test_recall_does_not_depend_on_weight`: a synthetic run with misses and moves; `tracked` and `false_ids` from `measure` are equal at 0.1 and 1.0.
  - `test_measure_reports_equal_truth`: reported equals `truth`, so `frame_err_px == 0` and `jitter_px == true_jitter_px`.
  - `test_measure_no_reports_is_nan`: an empty reported list gives `nan` errors and `tracked == 0`.
  - `test_steady_matrix`: the centre maps to itself; at zoom 2, the point `(0, 0)` of a 100 × 100 frame maps to `(-50, -50)`.
  - `test_summarise_mean_min_max`: two seeds with `frame_err_px` 1 and 3 give mean 2, min 1 and max 3. `nan` in a third row is ignored.
  - `test_detect_runs_generated`: `seeds=(1, 2)` gives `real == {0}` and `1 + 3 * 2` runs, with clean first.
  - `test_cache_path_includes_seeds`: `cache_path("x", (1, 2)) != cache_path("x", (1,))`.
  - `test_missing_footage_names_readme`: monkeypatch `FOOTAGE` to a missing path; `pytest.raises(FileNotFoundError, match="Test Footage")`.
- [ ] **Step 2: Run** `python -m pytest tests/test_smoothing_study.py -q`. Expected: FAIL on import.
- [ ] **Step 3: Implement** `study.py`. Write `analysis/requirements.txt` with the four packages pinned to their current releases (look them up), plus `-r ../requirements-dev.txt`. Update `.gitignore`.
- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`.
- [ ] **Step 5: Cross-check against the baseline.** In a one-off Python call, run `load_or_detect("fdcl-gwu", seeds=(1,))` and `summarise(sweep(...))`. Expected: moderate, weight 0.6 `frame_err_px_mean` ≈ 15.0 and `tracked` 54.1%; weight 1.0 ≈ 1.7. Log the numbers. If they differ, stop and find out why before going on.
- [ ] **Step 6: Commit** the new files, `.gitignore` and the test: "Add the smoothing study's data layer".

### Task 4: Plotly charts

**Files:**
- Create: `analysis/smoothing/charts.py`
- Test: `tests/test_smoothing_study.py` (add tests guarded by `pytest.importorskip("plotly")`)

**Interfaces:**
- Consumes: `summarise` rows, `trace` dict and `OUTPUT_DIR` (Task 3).
- Produces:
  - `metric_vs_weight(summary, footage, metric, title, y_title) -> go.Figure`: one line per level (mean) with a shaded min-max band, x = weight. Raw rows are left out.
  - `tradeoff(summary, footage, level="moderate") -> go.Figure`: x = `frame_err_px_mean`, y = `jitter_px_mean`, one point per weight labelled with the weight, plus a dashed horizontal line at the mean `true_jitter_px`.
  - `trace_chart(trace) -> go.Figure`: x = frame. Truth is a line, raw is markers, and each weight is a line with gaps where the marker is not reported.
  - `save(fig, name, png=True) -> list[Path]`: write `OUTPUT_DIR/name.html`, then try `name.png` (scale 2). If kaleido fails, print a warning naming the Chromium requirement and `plotly_get_chrome`, and return the HTML path only.
  - Every figure has a title, axis titles with units, and a legend. Use one fixed colour per level in all charts.

- [ ] **Step 1: Write failing tests:** `test_charts_have_one_trace_per_level` (on a summary built from synthetic rows, `metric_vs_weight` has a named trace per level), and `test_save_without_png_writes_html` (`save(fig, "t", png=False)` with `OUTPUT_DIR` monkeypatched to `tmp_path` writes `t.html` only).
- [ ] **Step 2: Run** `python -m pytest tests/test_smoothing_study.py -q` with plotly installed (`pip install -r analysis/requirements.txt`). Expected: the new tests fail. Without plotly they are skipped.
- [ ] **Step 3: Implement** `charts.py`.
- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`.
- [ ] **Step 5: Commit** `charts.py` and the test: "Add Plotly charts for the smoothing study".

### Task 5: Notebook, results and docs

**Files:**
- Create: `analysis/smoothing/smoothing_study.ipynb`, `analysis/README.md`
- Modify: `README.md` and `README.fr.md` (Project Structure: one line for `analysis/`; Test Footage: one sentence pointing at the notebook), `logs/DECISIONS.md`, `logs/2026-11-16-test-smoothing-study.md`

**Interfaces:**
- Consumes: everything in Tasks 3 and 4.

- [ ] **Step 1: Build the notebook** with `nbformat`, from a script in the scratchpad (not committed). Use Markdown cells for each numbered section, and keep each code cell to a few lines:
  1. **Smoothing and tracking under shake.** The question, and the Task 3 decision it informs.
  2. **Setup.** `pip install -r analysis/requirements.txt`, the footage pointer, and a cell that walks up from `Path.cwd()` to the folder holding `AGENTS.md`, adds it to `sys.path` and imports `study` and `charts`.
  3. **The variable.** The update `pos += w × (new − pos)`, with 1.0 meaning off. The gate tests the raw detection, so recall should not depend on `w`.
  4. **Method.** Shake levels (show `SHAKE_LEVELS`), seeds, weights, and detect-once-then-replay.
  5. **Measures.** Frame error, steady error, jitter and true jitter, recall and false IDs, each in one sentence.
  6. **fdcl-gwu: detect and sweep.** `load_or_detect`, `sweep`, `summarise`, and the `format_table` check that recall and false IDs are flat, with raw error included.
  7. **fdcl-gwu: results.** The frame error, steady error and jitter charts, the moderate trade-off, and the trace. Each chart is followed by a short Markdown note on how to read it.
  8. **Shadow-ArUco.** The same three sweep charts and the check table.
  9. **Export.** `save` every figure, and list the files.
  10. **Conclusion.** Findings in plain words with the numbers from this run, and further work (1€ filter, offline smoothing).
- [ ] **Step 2: Run it end to end:** `jupyter nbconvert --to notebook --execute analysis/smoothing/smoothing_study.ipynb --output-dir analysis/smoothing/output`. Expected: no errors, and the charts and PNGs exist in `output/`. Write the conclusion from these numbers, then rerun if the conclusion cell changed code.
- [ ] **Step 3: Clear outputs:** `jupyter nbconvert --clear-output --inplace analysis/smoothing/smoothing_study.ipynb`. Then run `./scripts/check.sh` (ruff lints the notebook). Expected: all `[OK]`.
- [ ] **Step 4: Write docs.** `analysis/README.md` covers what the folder is, how to install it, how to run the notebook, where the charts go, and how to refresh the cache. Add the same line to both READMEs. Add to DECISIONS: "2026-11-16: Analysis notebooks and their dependencies (`plotly`, `kaleido`, `nbformat`, `jupyter`) live in `analysis/`; CI and the drone do not install them." In the log, record the key numbers per footage at moderate shake (weights 0.6 and 1.0: frame error, steady error, jitter).
- [ ] **Step 5: Commit** the notebook, both READMEs, `analysis/README.md`, DECISIONS and the log: "Add the smoothing study notebook".

### Finish

- [ ] Fill in the log's Verification section with the check output, the vibration baseline recheck and the study's cross-check numbers. Mark anything not run, and note that nothing was run on hardware.
- [ ] Push `test/smoothing-study` to `origin` and open a pull request against `fzizzle/droneload-ESILV-2026-2027` `main`. Say what changed, how it was verified and what remains: the Task 3 decision on `SMOOTHING`, and flight footage.
