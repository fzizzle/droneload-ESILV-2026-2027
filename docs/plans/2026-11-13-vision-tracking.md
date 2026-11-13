# Vision Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept a marker only once it is seen in several recent frames, and smooth its pixel position, so wrong IDs and jitter stop reaching the CSV and the debug image.

**Architecture:** A pure-Python `MarkerTracker` in `droneload/vision/tracking/tracker.py` takes each frame's `(id, cx, cy)` list and returns the confirmed, smoothed list. `detect.main()` calls it after the size filter. `testing/benchmark.py` gains `--track` to score the tracker on the sequential Shadow-ArUco frames.

**Tech Stack:** Python standard library (`collections.deque`, `math.dist`), OpenCV, pytest. No new dependency.

**Spec:** `droneload/vision/tracking/README.md` (rows 1 and 2 of Planned Work: confirm across frames, smooth positions).

## Global Constraints

- Settings are constants at the top of `tracker.py`.
- Added delay: no more than a few frames (tracking README, Proposed).
- The CSV columns stay `timestamp_ms, id, label, cx, cy`. Values become the smoothed, confirmed positions; tell the reviewer this in the PR.
- `ARUCO_LABELS`, marker IDs and the default dictionary do not change.
- Detection change: run `python -m testing.benchmark` before and after, and log both. Baseline `found=56.4% unmatched=26.6%`.
- `README.md` and `README.fr.md` change together.
- Out of scope: skipping poor frames, drone-motion correction, whole-image stabilisation (rows 3 to 5 of Planned Work).

## Review Focus

1. The same ID detected twice in one frame (a false positive): the tracker follows the detection nearest its track and ignores the other, rather than alternating.
2. A marker leaves and comes back far away after a long gap: it must be confirmed again, not smoothed from its stale position.
3. A marker moving steadily at 20 px per frame: it still confirms and follows, within one jump limit.
4. Frames with no detections: tracks age and are removed once they have no hit left in the window.
5. A single-frame source, as in `test_size_filter`: tracking hides everything, so that test must run with `--no-track`.

---

### Task 1: MarkerTracker

**Files:**
- Create: `droneload/vision/tracking/__init__.py` (empty)
- Create: `droneload/vision/tracking/tracker.py`
- Test: `tests/test_tracking.py`

**Interfaces:**
- Produces: `MarkerTracker()` with `update(detections: list[tuple[int, float, float]]) -> list[tuple[int, float, float]]`, returning confirmed markers seen in this frame as `(id, cx, cy)`, sorted by ID, positions rounded to 0.1 px.
- Constants: `CONFIRM_FRAMES = 3`, `WINDOW_FRAMES = 5`, `MAX_JUMP_PX = 40.0`, `SMOOTHING = 0.6` (weight of the new position).

Algorithm, one track per ID:

```
for each ID in this frame's detections:
    pick the detection nearest the existing track (or the first if no track)
    if no track, or that detection is farther than MAX_JUMP_PX:
        start a new track at it, hits = [True]
    else:
        pos += SMOOTHING * (new - pos); hits.append(True)
for each track not seen this frame: hits.append(False)
remove tracks with no True left in hits (deque, maxlen=WINDOW_FRAMES)
return tracks seen this frame with sum(hits) >= CONFIRM_FRAMES
```

- [ ] **Step 1: Write the failing tests** in `tests/test_tracking.py`, each driving `MarkerTracker().update(...)` frame by frame:
  - `test_confirms_after_three_frames`: `[(4, 100, 100)]` three times; first two return `[]`, third returns one entry with ID 4.
  - `test_single_frame_flicker_never_reported`: ID 7 in frame 1 only, then four empty frames; every return is `[]`.
  - `test_smooths_position`: three frames at `(0, 0)` then one at `(10, 0)`; last return is `[(1, 6.0, 0.0)]`.
  - `test_jump_restarts_confirmation`: three frames at `(0, 0)`, then `(200, 0)`; last return is `[]`.
  - `test_brief_gap_keeps_track`: frames hit, hit, hit, miss, hit at `(50, 50)`; last return has ID 2.
  - `test_expires_after_window`: three hits, five empty frames, one hit at the same place; last return is `[]`.
  - `test_duplicate_id_follows_nearest`: confirm ID 3 at `(100, 100)`, then a frame with `(3, 400, 400)` and `(3, 102, 100)`; return has one ID 3 entry with `cx` between 100 and 102.
  - `test_follows_steady_motion`: ID 5 moving `+20` px in x for 10 frames; returns from frame 3 on contain ID 5.
  - `test_output_sorted_by_id`: IDs 9 and 0 for three frames; last return IDs are `[0, 9]`.

- [ ] **Step 2: Run them to verify they fail**
  Run: `python -m pytest tests/test_tracking.py -q`
  Expected: FAIL, `ModuleNotFoundError: droneload.vision.tracking.tracker`.

- [ ] **Step 3: Implement `MarkerTracker` in `droneload/vision/tracking/tracker.py`** following the algorithm above. A small `_Track` dataclass holding `cx`, `cy` and `hits` is enough.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `./scripts/check.sh`
  Expected: all `[OK]`.

- [ ] **Step 5: Commit**
  ```bash
  git add droneload/vision/tracking/__init__.py droneload/vision/tracking/tracker.py tests/test_tracking.py
  git commit -m "Add a marker tracker that confirms and smooths detections"
  ```

### Task 2: Benchmark with tracking

**Files:**
- Modify: `testing/benchmark.py` (`score()` and `main()`)
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Consumes: `MarkerTracker.update()` from Task 1.
- Produces: `score(paths, detector, tracker=None) -> tuple[int, int, int]`. With a tracker, paths are fed in sorted order and the matched/unmatched counts use the tracker's output instead of raw detections. `main()` gains `--track`.

- [ ] **Step 1: Write the failing test** `test_score_with_tracker_drops_flicker` in `tests/test_benchmark.py`. In `tmp_path`, write five 640 × 480 white PNGs with a `DICT_4X4_50` marker ID 0 (150 px) at the same place in all five, and marker ID 1 only in frame 3. Write `corrected_annotations/<name>.json` for each, listing both markers' true corners only where drawn (format: `{"markers": [{"id": 0, "corners": [{"x":..,"y":..}, ...]}]}`). Assert:
  - `score(paths, detector)` gives `matched == 6`, `unmatched == 0`.
  - `score(paths, detector, MarkerTracker())` gives `matched == 3` (ID 0 in frames 3 to 5), `unmatched == 0`.

- [ ] **Step 2: Run it to verify it fails**
  Run: `python -m pytest tests/test_benchmark.py -q`
  Expected: FAIL, `score()` takes no `tracker`.

- [ ] **Step 3: Add the `tracker` parameter and `--track` flag.** Build `(id, cx, cy)` from each frame's corners, pass it through `tracker.update()` when given, then match as today.

- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`.

- [ ] **Step 5: Measure and tune.** Run `python -m testing.benchmark` and `python -m testing.benchmark --track`. Try `CONFIRM_FRAMES` 2 and 3 and `SMOOTHING` 0.6 and 1.0 (no smoothing); keep the setting with the lowest `unmatched` that loses at most 5 points of `found`. Record every result in the branch log. If no setting lowers `unmatched`, stop and report it before Task 3.

- [ ] **Step 6: Commit**
  ```bash
  git add testing/benchmark.py tests/test_benchmark.py droneload/vision/tracking/tracker.py
  git commit -m "Score the tracker in the benchmark"
  ```

### Task 3: Use the tracker in the detection loop

**Files:**
- Modify: `droneload/vision/detect.py` (`main()`)
- Modify: `tests/test_detect.py` (`test_size_filter` argv)
- Modify: `droneload/vision/tracking/README.md`, `droneload/vision/README.md`, `README.md`, `README.fr.md`, `logs/DECISIONS.md`
- Test: `tests/test_detect.py`

**Interfaces:**
- Consumes: `MarkerTracker` from Task 1.
- Produces: CLI flag `--no-track` on `python -m droneload.vision`. With tracking on, the CSV, terminal log and debug image show only the tracker's output; the drawn outline is the raw corners of each confirmed ID.

- [ ] **Step 1: Write the failing test** `test_single_frame_needs_no_track` in `tests/test_detect.py`, reusing the `FakeCamera` pattern from `test_size_filter` with one frame holding marker 0: with argv `["detect"]` the CSV has no rows; with `["detect", "--no-track"]` it logs ID 0. Change `test_size_filter`'s argv to `["detect", "--no-track"]`.

- [ ] **Step 2: Run it to verify it fails**
  Run: `python -m pytest tests/test_detect.py -q`
  Expected: FAIL, unknown argument `--no-track`.

- [ ] **Step 3: Wire it in.** In `main()`, after the size filter, pass `detected_info`'s `(id, cx, cy)` through one `MarkerTracker` created before the loop, unless `--no-track`; keep the corners of confirmed IDs for drawing. Do not call `update()` on failed reads.

- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`, including `test_generated_video_end_to_end` (150 frames, so all 3 IDs confirm).

- [ ] **Step 5: Update docs.**
  - `tracking/README.md`: status of rows 1 and 2, the chosen constants and the benchmark results.
  - `vision/README.md`: one line under Measured So Far with the `--track` result.
  - `README.md` and `README.fr.md`: `--no-track` in the options section, and `tracking/` no longer "Planned" in the file tree.
  - `logs/DECISIONS.md`: one line, e.g. "2026-11-xx: Detection reports a marker only after it is seen in 3 of the last 5 frames; `--no-track` turns this off."

- [ ] **Step 6: Commit**
  ```bash
  git add droneload/vision/detect.py tests/test_detect.py droneload/vision/tracking/README.md droneload/vision/README.md README.md README.fr.md logs/DECISIONS.md
  git commit -m "Report only confirmed, smoothed markers in the detection loop"
  ```
