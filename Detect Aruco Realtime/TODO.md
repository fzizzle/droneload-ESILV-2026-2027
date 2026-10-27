# TODO

Problems found while reviewing the project.

## Bugs

- [ ] **Camera test checks a different pipeline from `main.py`.**
  `test_camera.sh` uses `video/x-raw(memory:GBM)` + `qtivtransform`, while
  `camera_rubikpi_csi.py` uses plain `video/x-raw` NV12 + `videoconvert`.
  A passing test does not prove `main.py` can open the camera. Make both use
  the same pipeline (ideally whichever one actually works on the board).

- [ ] **`test_camera.sh` reports FAILED on Ctrl+C.**
  `[ $? -eq 0 ] || [ $? -eq 130 ]` — the second `$?` holds the result of the
  first `[`, not of `gst-launch-1.0`, so exit code 130 never matches.
  Save the code first: `rc=$?` then test `$rc`.

- [ ] **`setup.sh` step 4 checks OpenCV before it is built.**
  On a fresh board `import cv2` fails or finds the wrong OpenCV, giving a
  misleading warning. Move the OpenCV/GStreamer check to after
  `build_opencv.sh`, or drop it (that script already verifies).

- [ ] **Debug image shows markers that are filtered out.**
  `drawDetectedMarkers` runs before the `MIN_SIDE_PX` filter. Draw only the
  markers that pass the filter.

## Repo hygiene

- [ ] **`rubikpi-script` is a broken submodule.** It is committed as a gitlink
  with no `.gitmodules`, so clones get an empty folder. `setup.sh` clones it
  into `~` anyway — remove it from the repo (`git rm --cached`).

- [ ] **Generated files are committed:** `__pycache__/`, `aruco_debug.jpg`,
  `detections.csv`. Remove them and add a `.gitignore`.

- [ ] **`README.md` is UTF-16.** It shows garbled in `cat`, `grep` and diffs.
  Convert it to UTF-8.

## Cleanup

- [ ] **Stale commented-out import in `main.py`:**
  `from camera_rubikpi import RubikPiCamera` — the file is
  `camera_rubikpiusb.py`.

- [ ] **CLAHE is recreated every frame** in `preprocess()`. Create it once at
  startup (minor performance win).

## Possible features

- [ ] Output is pixel centre only — no pose/distance estimation and nothing is
  sent to a flight controller. Consider `estimatePoseSingleMarkers`/`solvePnP`
  with a camera calibration if the drone needs to act on detections.
