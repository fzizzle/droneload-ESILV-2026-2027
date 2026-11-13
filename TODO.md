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
  footage does not use `DICT_4X4_50`. Tracking cuts unmatched detections to 2.7%, with
  53.2% found.

- [ ] **Record real `DICT_4X4_50` footage.** No public source was found.

- [ ] **Add a camera calibration tool.** Plan: `docs/plans/2026-11-13-camera-calibration.md`.
  `pose.py` needs a calibration file with
  `camera_matrix` and `dist_coeffs`. Use OpenCV's checkerboard calibration.

- [ ] **Use marker positions in the detection loop.** This may change the CSV
  format, which needs a person's decision.

- [ ] **Measure vibration in flight.** `testing/vibration_test.py` is simulated.
  Record markers from a flying drone, and set a fixed short exposure on live
  cameras. Only `camera_picamera2.py` sets exposure today.

- [x] **Update `ARUCO_LABELS` for the V0 rules.** Labels now cover IDs 0-9.

- [x] **Simulate indoor positioning.** The simulator flies on optical flow and
  a rangefinder, without GPS.

- [ ] **Simulate Marvelmind beacons** as a second position source.

- [ ] **Set the indoor origin to the venue.** `flight` sends the simulator's
  home as the estimator's origin; the compass check fails if they differ.

- [ ] **Set PMW3901 and rangefinder drivers** in `stabilisation/indoor.parm`
  once the rangefinder is known. Only simulator drivers exist.

- [x] **Stop the drone if the mission stops sending commands.** ArduPilot's
  GCS failsafe lands after 3 s without a heartbeat. Check it on the Pixhawk
  with propellers off.

- [ ] **Decide when `flight` may connect to a real drone.** It refuses
  anything but a local simulator. Needs a person's decision and a
  propellers-off bench test first.

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

- [ ] **Confirm the Qualcomm computer's exact model.** Do this before buying
  cameras.
- [ ] **Buy two cameras:** one downward, one forward, preferably global shutter,
  in colour, because vibration distorts rolling-shutter images and the path and
  posters need colour. If the board is a Rubik Pi 3, prefer USB (UVC) cameras,
  starting with the Arducam AR0234. Check fixed exposure on the board before
  buying the second.
- [ ] **Camera damping:** soft mounts for both cameras, and spare propellers to
  balance.
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

## Can be built before hardware

Each runs on a PC, against the simulator, recorded footage or a stub. Items
already listed above are not repeated: calibration tool, `DICT_4X4_50`
footage and Marvelmind simulation.

- [x] **Tracking in `vision/tracking`.** Confirm markers across frames and
  smooth their positions. Skipping blurred frames and using drone motion are
  still open; see `droneload/vision/tracking/README.md`.
- [ ] **`comms` protocol layer.** A state machine for the V0 robot protocol
  (`D`/`G`/`A` commands, `N`/`F`/`S` replies, target digit), tested against a
  fake serial port. `pyserial` is a new dependency and needs a person's OK.
- [ ] **`mission` state machine.** Steps, timeouts and the "operator only
  confirms" rule, run against stubbed modules.
- [ ] **Poster and floor-line vision.** Prototype A3 target recognition, decoy
  rejection and safe-path line detection on synthetic or phone images.
- [ ] **`navigation` in the simulator.** Centre over a marker, follow a path
  and cross the window, using simulated detections. It commands a simulated
  drone, so it needs a person's OK first.
- [ ] **Detection display for the jury.** `--show` and `--record` give an
  annotated video on a PC. Still to decide: how it reaches the organisers'
  screen from the drone.
- [ ] **Drop-accuracy bench test.** 20 drops each from 0.5, 1 and 1.5 m of a
  50 g disc onto an A3 sheet, to help choose the grabber.

## Possible features

- [ ] Output is pixel centre only — no pose/distance estimation and nothing is
  sent to a flight controller. Consider `estimatePoseSingleMarkers`/`solvePnP`
  with a camera calibration if the drone needs to act on detections.
