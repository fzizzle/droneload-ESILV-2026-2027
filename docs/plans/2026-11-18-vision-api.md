# Vision API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let other modules ask `vision` what a frame contains. Today the only way in is the command-line loop in `detect.py`, and its CSV is a log with a 1 s cooldown, not a signal a controller can use.

**Architecture:** `detect.py` gains a `MarkerDetector` class whose `process(frame)` does what the loop body does now: grey conversion, CLAHE, detection, size filter, tracking and, with a calibration, each marker's position in metres. `main()` becomes a thin loop around it, with unchanged output. A small wrapper camera keeps only the newest frame, so a controller never acts on a stale one.

**Tech Stack:** OpenCV, numpy, the standard library's `threading`. No new dependency.

**Spec:** `docs/plans/2026-11-18-roadmap.md`, "Shared Interfaces".

## Global Constraints

- **The CSV format, marker IDs, labels and default dictionary do not change.** `detections.csv` keeps its columns and values, and `aruco_debug.jpg` and the terminal output stay the same.
- This is a detection-path change: run `python -m testing.benchmark` and `python -m testing.benchmark --track` before and after and log both. Expected: `found=57.6% unmatched=4.1%` and `found=54.8% unmatched=0.8%`, unchanged.
- Run the vibration baseline before and after: moderate `raw=65.9% tracked=57.2%`, unchanged.
- Existing tests in `tests/test_detect.py` pass without edits, apart from imports.
- Settings stay as constants at the top of `detect.py`.
- Branch `feature/vision-api`, log `logs/YYYY-MM-DD-feature-vision-api.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **The same ID detected twice in a frame:** `process()` must attach the corners nearest the tracker's reported position, as the loop does now. Test `test_duplicate_id_keeps_nearest_corners` (Task 1).
2. **A grey frame passed in:** `process()` must not call `cvtColor` on it. Test `test_process_accepts_grey` (Task 1).
3. **A calibration made at another resolution:** `MarkerDetector` must refuse it rather than return wrong distances. Test `test_calibration_size_mismatch` (Task 2).
4. **A camera that stops delivering:** `LatestFrameCamera.read()` must return `(False, None)` rather than repeat the last frame for ever. Test `test_no_new_frame_is_a_miss` (Task 3).
5. **`release()` while the reader thread is inside `read()`:** it must return within 1 s and leave no thread running. Test `test_release_stops_the_thread` (Task 3).

---

### Task 1: `MarkerDetector` and `annotate`

**Files:**
- Modify: `droneload/vision/detect.py` (new classes; `main()` lines 183-242 call them)
- Modify: `testing/benchmark.py`, `testing/vibration_test.py` only if they can use `process()` with identical scores; otherwise leave them
- Test: `tests/test_detect.py`

**Interfaces:**
- Produces: `Marker`, `MarkerFrame`, `MarkerDetector(dict_name=ARUCO_DICT, track=True, calibration=None)` with `process(frame) -> MarkerFrame`, and `annotate(frame, marker_frame, status="") -> np.ndarray`, exactly as in the roadmap. `annotate` returns a copy with rejected outlines in `REJECTED_COLOR`, confirmed markers outlined with their IDs, and `status` drawn where `draw_status` draws now.

- [ ] **Step 1: Record the before numbers** for both benchmarks and the vibration baseline in the log.

- [ ] **Step 2: Write the failing tests.** Use the existing `one_marker_frame()` helper.

  - `test_process_reports_a_marker`: with `track=False`, one frame gives one `Marker` whose `id`, `label`, `cx`, `cy` equal what `center_of` and `ARUCO_LABELS` give, `corners.shape == (4, 2)`, and `offset_m is None`.
  - `test_process_confirms_across_frames`: with `track=True`, frames 1 and 2 give no markers and one `rejected` entry each; frame 3 gives the marker.
  - `test_process_applies_the_size_filter`: a marker with a side under `MIN_SIDE_PX` appears in neither list.
  - `test_process_accepts_grey`: a grey frame gives the same marker as its BGR copy.
  - `test_duplicate_id_keeps_nearest_corners`: after confirming ID 0 at the left, a frame holding ID 0 at the left and again at the right returns the left corners.
  - `test_annotate_draws_and_copies`: the result differs from the input frame, and the input is unchanged.

- [ ] **Step 3: Run them and check they fail.** `python -m pytest tests/test_detect.py -q -k "process or annotate or duplicate"`.

- [ ] **Step 4: Implement the classes, and make `main()` use them.** Move the loop body's detection, filtering, tracking and corner matching into `process()`, and the drawing into `annotate()`. The CSV write, cooldown, recording, `--show` pacing and terminal log stay in `main()`.

- [ ] **Step 5: Run `./scripts/check.sh`, then the benchmarks and the vibration baseline.** Expected: checks pass, and all three scores equal the before numbers. Log them.

- [ ] **Step 6: Commit.** Message "Add MarkerDetector.process so other modules can read detections".

### Task 2: Positions in metres

**Files:**
- Modify: `droneload/vision/detect.py`, `droneload/vision/pose.py` (`load_calibration` also returns the image size)
- Test: `tests/test_detect.py`, `tests/test_calibrate.py` if `load_calibration`'s return changes there
- Docs: `droneload/vision/README.md` (Status, and "not yet used by the detection loop"), `README.md` and `README.fr.md` (Usage: the new option), `TODO.md` ("Use marker positions in the detection loop", "Possible features")

**Interfaces:**
- Consumes: `pose.marker_offset(corner, camera_matrix, dist_coeffs)`.
- Produces: `MarkerDetector(calibration=path_or_None)`; with a path, every `Marker.offset_m` is `(x, y, z)` in the camera frame. Command line: `--calibration FILE`. With it, the terminal log adds `offset=(x, y, z) m` per marker. **The CSV does not change.**
- `pose.load_calibration(path) -> (camera_matrix, dist_coeffs, (width, height))`.

- [ ] **Step 1: Write the failing tests.**

  - `test_process_gives_offsets`: render a marker with `testing.sim_camera.render_down` from 1.5 m, 0.3 m south of it; with a calibration file written from `sim_camera.CAMERA_MATRIX`, `offset_m` is within 2 cm of `(0.0, -0.3, 1.5)`. If the sim-camera plan is not merged, build the frame with `cv2.warpPerspective` as `tests/test_detect.py` already does for pose tests.
  - `test_calibration_size_mismatch`: a calibration recorded at 640 × 480 and a 1280 × 720 frame make `process()` raise `ValueError` naming both sizes.
  - `test_csv_unchanged_with_calibration`: a run of `main()` with `--calibration` writes the same header and row values as one without.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.** Compute offsets only for confirmed markers.
- [ ] **Step 4: Run `./scripts/check.sh` and both benchmarks.** Expected: unchanged scores.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Report marker positions in metres when a calibration is given".

### Task 3: Latest-frame camera

**Files:**
- Create: `droneload/vision/camera_latest.py`
- Test: `tests/test_camera_latest.py`
- Docs: `README.md` and `README.fr.md` (Project Structure), `TODO.md` ("Set MJPG and a buffer of one frame": note this covers the stale-frame half)

**Interfaces:**
- Produces:

```python
class LatestFrameCamera:
    """Wraps any camera. A thread reads it continuously; read() returns only the newest frame."""
    def __init__(self, camera): ...
    finite = False
    frame_time = None            # time.monotonic() when the newest frame arrived
    def open(self) -> bool
    def read(self) -> tuple      # (True, frame) once per new frame, else (False, None)
    def release(self) -> None
```

- [ ] **Step 1: Write the failing tests,** with a fake camera that returns numbered frames at a set interval.

  - `test_read_returns_the_newest_frame`: after the fake has produced 5 frames, one `read()` returns frame 5.
  - `test_no_new_frame_is_a_miss`: a second `read()` straight after returns `(False, None)`.
  - `test_frame_time_is_set`: `frame_time` is within 0.1 s of `time.monotonic()` after a read.
  - `test_open_failure_passes_through`: when the wrapped `open()` returns `False`, so does the wrapper, and no thread starts.
  - `test_release_stops_the_thread`: `release()` returns within 1 s and `threading.active_count()` is back to its starting value.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement** with one daemon thread, a lock around the stored frame, and an event that `release()` sets. Do not wrap finite sources: `detect.make_camera` keeps files unwrapped so benchmarks stay frame-exact.
- [ ] **Step 4: Run `./scripts/check.sh`.**
- [ ] **Step 5: Update the docs and commit.** Message "Add a camera wrapper that keeps only the newest frame".

## Done When

- [ ] `MarkerDetector().process(frame)` works from a Python prompt with no other setup.
- [ ] Benchmarks and the vibration baseline are unchanged, with before and after in the log.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## Not in This Plan

- Two cameras at once. `mission` opens one `MarkerDetector` per camera; nothing here needs to change.
- Any change to what is detected. See `docs/plans/2026-11-18-detection-tuning.md`.
