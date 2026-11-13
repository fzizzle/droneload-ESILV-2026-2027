# Camera Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A command, `python -m droneload.vision.calibrate`, that finds a printed checkerboard in frames from any camera source and writes the calibration file `pose.load_calibration()` reads, so `marker_offset()` gives real distances in metres.

**Architecture:** `droneload/vision/calibrate.py` holds small functions (find the board, calibrate, save) and a `main()` that reads frames through the existing `detect.make_camera()`, keeps well-spaced frames where the board is found, and writes OpenCV YAML. Tests render a checkerboard through a known camera, so calibration can be checked against the true values without hardware.

**Tech Stack:** OpenCV (`findChessboardCornersSB`, `calibrateCamera`, `FileStorage`), NumPy, pytest. No new dependency.

**Spec:** `TODO.md`, "Add a camera calibration tool": `pose.py` needs a calibration file with `camera_matrix` and `dist_coeffs`; use OpenCV's checkerboard calibration. `droneload/vision/README.md`, Position Accuracy: real accuracy depends on calibration.

## Global Constraints

- The file must load with the existing `pose.load_calibration(path)`: OpenCV YAML with keys `camera_matrix` (3 × 3) and `dist_coeffs`.
- Hardware-independent: frames come from `detect.make_camera(source)`, so the tool works for webcams, video files, image sequences, `rubikpi-csi` and `picamera`.
- Settings are constants at the top of `calibrate.py`.
- Board default: 9 × 6 inner corners (a 10 × 7 square board), 25 mm squares; both can be changed on the command line, because the printed size must be measured.
- No change to `pose.py`, `detect.py`, the CSV, marker IDs or the dictionary.
- Calibration files are not committed for now (`camera.yaml` added to `.gitignore`); where real camera files live is a later decision.
- `README.md` and `README.fr.md` change together.

## Review Focus

1. A source where the board is never found, such as the wrong `--board` size: the tool exits with an error naming the board size it looked for, and writes no file.
2. A video of a board held still: near-identical frames are not all kept, because frames are spaced at least `MIN_GAP_FRAMES` apart.
3. A poor calibration (blurred or few angles): the RMS error is printed, and above `MAX_RMS_PX` a warning says to recalibrate; the file is still written.
4. Calibrating at one resolution and using it at another: the file records `image_width` and `image_height`, so a mismatch can be detected later.
5. A board seen from only one angle: covered by the rendered views in the tests, which vary tilt, so the tests show what a good set of views looks like; the README says to tilt the board.

---

### Task 1: Calibration functions

**Files:**
- Create: `droneload/vision/calibrate.py`
- Create: `tests/test_calibrate.py`

**Interfaces:**
- Produces, in `droneload/vision/calibrate.py`:
  - Constants: `BOARD_INNER_CORNERS = (9, 6)`, `SQUARE_SIZE_M = 0.025`, `TARGET_FRAMES = 20`, `MIN_FRAMES = 10`, `MIN_GAP_FRAMES = 15`, `MAX_RMS_PX = 1.0`, `OUTPUT_PATH = "camera.yaml"`.
  - `board_points(inner_corners, square_size_m) -> np.ndarray`: shape `(cols * rows, 3)`, float32, z = 0, in the order `findChessboardCornersSB` returns corners.
  - `find_board(gray, inner_corners) -> np.ndarray | None`: corners of shape `(N, 1, 2)` float32, or `None`. Use `cv2.findChessboardCornersSB` (subpixel accurate, no separate `cornerSubPix`).
  - `calibrate(image_points, image_size, inner_corners, square_size_m) -> tuple[np.ndarray, np.ndarray, float]`: `(camera_matrix, dist_coeffs, rms_px)` from `cv2.calibrateCamera`. Raises `ValueError` if `len(image_points) < MIN_FRAMES`, with both numbers in the message.
  - `save_calibration(path, camera_matrix, dist_coeffs, image_size, rms_px) -> None`: writes keys `camera_matrix`, `dist_coeffs`, `image_width`, `image_height`, `rms_px` with `cv2.FileStorage`.

- [ ] **Step 1: Write the failing tests** in `tests/test_calibrate.py`.
  Test helper `render_board(rvec, tvec) -> np.ndarray`: a 1280 × 720 grey image of a 10 × 7 checkerboard with 25 mm squares and a white margin of one square, projected with `CAMERA_MATRIX = [[900, 0, 640], [0, 900, 360], [0, 0, 1]]` and no distortion (same approach as `render_marker` in `tests/test_detect.py`: project the board's outer corners, `getPerspectiveTransform`, `warpPerspective` with white border).
  Helper `views(n)`: `rng = np.random.default_rng(0)`; draw `rvec` with x and y in ±0.5 rad and z in ±0.3 rad, `tvec` with x ±0.05 m, y ±0.03 m and z 0.4 to 0.7 m; redraw until all four outer corners project at least 40 px inside the image. Return `n` `(rvec, tvec)` pairs.
  - `test_board_points_shape_and_spacing`: `board_points((9, 6), 0.025)` has shape `(54, 3)`, `[1] - [0] == (0.025, 0, 0)`, all z are 0.
  - `test_find_board_on_rendered_view`: one view; result has shape `(54, 1, 2)`.
  - `test_find_board_none_on_blank`: a white 1280 × 720 image returns `None`.
  - `test_calibrate_recovers_known_camera`: 15 views, `find_board` on each, `calibrate(...)`; `fx` and `fy` within 2% of 900, `cx` within 10 px of 640, `cy` within 10 px of 360, `rms_px < 0.5`.
  - `test_calibrate_rejects_too_few_frames`: 5 views raise `ValueError` matching `"5"` and `"10"`.
  - `test_saved_calibration_loads_in_pose`: save, then `pose.load_calibration(path)` returns an equal matrix; `FileStorage` reads `image_width == 1280`, `image_height == 720`, and `rms_px`.

- [ ] **Step 2: Run them to verify they fail**
  Run: `python -m pytest tests/test_calibrate.py -q`
  Expected: FAIL, `ModuleNotFoundError: droneload.vision.calibrate` (or `ImportError`).

- [ ] **Step 3: Implement the four functions** in `droneload/vision/calibrate.py`. `image_size` is `(width, height)` throughout.

- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`.

- [ ] **Step 5: Commit**
  ```bash
  git add droneload/vision/calibrate.py tests/test_calibrate.py
  git commit -m "Add checkerboard calibration functions"
  ```

### Task 2: Command line, end-to-end check and docs

**Files:**
- Modify: `droneload/vision/calibrate.py` (add `main()` and `if __name__ == "__main__"`)
- Modify: `tests/test_calibrate.py`
- Modify: `.gitignore`, `droneload/vision/README.md`, `README.md`, `README.fr.md`, `TODO.md`, `logs/DECISIONS.md`

**Interfaces:**
- Consumes: Task 1 functions and constants; `detect.make_camera(source)` (returns an object with `open()`, `read() -> (ok, frame)`, `release()`, and `finite`).
- Produces: `python -m droneload.vision.calibrate [--source SOURCE] [--board 9x6] [--square 0.025] [--frames 20] [--output camera.yaml]`.

Loop: read frames until `--frames` are kept or a finite source ends. A frame is kept when `find_board` succeeds and at least `MIN_GAP_FRAMES` frames have passed since the last kept frame. Print `captured k/N` on each keep. Then calibrate and save, and print the RMS and the matrix's `fx`, `fy`, `cx`, `cy`. If RMS > `MAX_RMS_PX`, print a `[WARNING]` line saying to recalibrate with sharper frames and more tilt. If fewer than `MIN_FRAMES` were kept, print `[ERROR]` naming the board size and exit with code 1, writing nothing. Ctrl+C stops capture and calibrates with what was kept.

- [ ] **Step 1: Write the failing tests** in `tests/test_calibrate.py`. Write rendered views to `tmp_path/frames/%03d.png` and pass that pattern as `--source`.
  - `test_main_writes_calibration`: 20 distinct views, `MIN_GAP_FRAMES` monkeypatched to 1; after `main()`, `--output` exists and its `fx` is within 2% of 900.
  - `test_main_spaces_frames`: one view repeated 30 times, default `MIN_GAP_FRAMES` (15) and `MIN_FRAMES` monkeypatched to 1; the file is written from 2 kept frames (check the `captured 2/` line in `capsys`).
  - `test_main_fails_without_board`: 12 blank frames; `SystemExit` with code 1, no output file, and the `[ERROR]` line contains `9x6`.
  - `test_main_warns_on_high_rms`: as the first test with `MAX_RMS_PX` monkeypatched to 0; output contains `[WARNING]` and the file is written.
  - `test_calibrated_pose_distance`: calibrate from 15 rendered views, then `pose.marker_offset` on `render_marker((0.1, 0.0, 1.5))` (import it from `tests.test_detect` or move it to a shared helper) gives z within 3% of 1.5.

- [ ] **Step 2: Run them to verify they fail**
  Run: `python -m pytest tests/test_calibrate.py -q`
  Expected: the `main` tests FAIL with `AttributeError: ... has no attribute 'main'`; `test_calibrated_pose_distance` may already pass, since it uses only Task 1 code. That is fine: it checks the chain, not new code.

- [ ] **Step 3: Implement `main()`** as described above, using `argparse`; parse `--board` as `"<cols>x<rows>"`.

- [ ] **Step 4: Run** `./scripts/check.sh`. Expected: all `[OK]`.

- [ ] **Step 5: Smoke test on a webcam, if one is available.** Show a checkerboard on a phone or a printout, run `python -m droneload.vision.calibrate --source 0`, and record the RMS in the branch log. If no webcam is available, say so in the log; this is not a test of the drone's camera either way.

- [ ] **Step 6: Update docs.**
  - `.gitignore`: add `camera.yaml`.
  - `droneload/vision/README.md`: a Calibration section: print a 10 × 7 checkerboard, measure one square and pass it with `--square`, hold it flat, move and tilt it across the whole image, aim for RMS under 1 px, recalibrate after changing resolution, lens or focus. Note that it has been tested only on rendered images (and the webcam, if Step 5 ran).
  - `README.md` and `README.fr.md`: the command and its options, next to the detection options.
  - `TODO.md`: tick "Add a camera calibration tool"; add "Decide where real camera calibration files are kept".
  - `logs/DECISIONS.md`: one line: checkerboard 9 × 6 inner corners, 25 mm by default, OpenCV YAML with `image_width`, `image_height` and `rms_px`.

- [ ] **Step 7: Commit**
  ```bash
  git add droneload/vision/calibrate.py tests/test_calibrate.py .gitignore droneload/vision/README.md README.md README.fr.md TODO.md logs/DECISIONS.md
  git commit -m "Add a calibration command that writes the file pose.py reads"
  ```

## Not in this plan

- ChArUco boards, which tolerate a partly hidden board. Try them only if checkerboard calibration proves awkward with the real camera.
- A live preview window while capturing. `--show` exists for detection; add it here if people struggle to aim the board.
- Using marker positions in the detection loop. That is its own TODO item and may change the CSV.
