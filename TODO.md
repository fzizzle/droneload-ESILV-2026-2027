# TODO

Problems found while reviewing the project.

## Bugs

- [ ] **Confirm the camera pipeline on the board.**
  `test_camera.sh` now uses the same pipeline as `camera_rubikpi_csi.py`
  (plain `video/x-raw` NV12 + `videoconvert`), but it has not been run on a
  RubikPi. If it fails, try `video/x-raw(memory:GBM)` + `qtivtransform` in both.

- [x] **`test_camera.sh` reports FAILED on Ctrl+C.**
  `[ $? -eq 0 ] || [ $? -eq 130 ]` — the second `$?` holds the result of the
  first `[`, not of `gst-launch-1.0`, so exit code 130 never matches.
  Save the code first: `rc=$?` then test `$rc`.

- [x] **`setup.sh` step 4 checks OpenCV before it is built.**
  On a fresh board `import cv2` fails or finds the wrong OpenCV, giving a
  misleading warning. Move the OpenCV/GStreamer check to after
  `build_opencv.sh`, or drop it (that script already verifies).

- [x] **Debug image shows markers that are filtered out.**
  `drawDetectedMarkers` runs before the `MIN_SIDE_PX` filter. Draw only the
  markers that pass the filter.

- [x] **`build_opencv.sh` GStreamer check reads a fixed slice of build info.**
  OpenCV pads that line, so the slice can miss `YES`. Check the whole
  `GStreamer:` line instead.

- [x] **Camera was hard-coded in `main.py`.** Replaced by `--source`.

- [ ] **Check false positives and missed markers on real footage.**
  On Shadow-ArUco `video_5` the detector found 56% of annotated markers, and
  27% of its detections did not match the annotations. Those detections
  include recurring wrong IDs. The cause has not been investigated, and this
  footage does not use `DICT_4X4_50`.

- [ ] **Record real `DICT_4X4_50` footage.** No public source was found.

- [ ] **Measure vibration in flight.** `testing/vibration_test.py` is simulated.
  Record markers from a flying drone, and set a fixed short exposure on live
  cameras. Only `camera_picamera2.py` sets exposure today.

- [x] **Update `ARUCO_LABELS` for the V0 rules.** Labels now cover IDs 0-9.

## Repo hygiene

- [x] **`rubikpi-script` is a broken submodule.** It is committed as a gitlink
  with no `.gitmodules`, so clones get an empty folder. `setup.sh` clones it
  into `~` anyway — remove it from the repo (`git rm --cached`).

- [x] **Generated files are committed:** `__pycache__/`, `aruco_debug.jpg`,
  `detections.csv`. Remove them and add a `.gitignore`.

- [x] **`README.md` is UTF-16.** It shows garbled in `cat`, `grep` and diffs.
  Convert it to UTF-8.

## Cleanup

- [x] **Stale commented-out import in `main.py`:**
  `from camera_rubikpi import RubikPiCamera` — the file is
  `camera_rubikpiusb.py`.

- [x] **CLAHE is recreated every frame** in `preprocess()`. Create it once at
  startup (minor performance win).

## Hardware to get

Not in the loan kit. Team 450's drone is going back to the organisers, so do
not count on anything fitted to it. Check what stays with us before buying: the
inventory marks some box items as present and does not record others.

- [ ] **Two cameras:** one downward, one forward, preferably global shutter,
  because vibration distorts rolling-shutter images. Team 450 used InnoMaker GS
  IMX296 modules; whether we have them is not recorded.
- [ ] **Camera damping:** soft mounts for both cameras, and spare propellers to
  balance.
- [ ] **Companion computer:** request the kit's, which the slides show as a
  Raspberry Pi 3 B+, or get something faster. Team 450's Raspberry Pi 4 is not
  recorded in the box inventory.
- [ ] **Grabber:** choose one first. Two Namvo KK-P20 electromagnets are in the
  box. Team 450's claw parts are not.
- [ ] **Rangefinder:** a ToF sensor is in the box; confirm it works. Buy one
  only if it does not.
- [ ] **Level converter:** needed between a 3.3 V Raspberry Pi and a 5 V
  Arduino or robot link. Team 450's is not recorded in the box.
- [ ] **Robot link:** V0 shows a team module on the robot. Team 450 used two
  HC-12 radio modules, which are not recorded in the box.
- [ ] **Test supplies:** printed `DICT_4X4_50` markers (20 × 20 cm), A3 posters
  and a camera calibration checkerboard.

## Possible features

- [ ] Output is pixel centre only — no pose/distance estimation and nothing is
  sent to a flight controller. Consider `estimatePoseSingleMarkers`/`solvePnP`
  with a camera calibration if the drone needs to act on detections.
