# TODO

Problems found while reviewing the project.

## Bugs

- [ ] **Check camera reopening on hardware.** The loop reopens a camera after 2 s without frames; this is tested with a fake camera only.
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
  11% of its detections did not match the annotations. Those detections
  include recurring wrong IDs. The cause has not been investigated, and this
  footage does not use `DICT_4X4_50`. Tracking cuts unmatched detections to 1.4%, with
  53.3% found.

- [ ] **Record real `DICT_4X4_50` footage.** No public source was found.

- [x] **Add a camera calibration tool.** `python -m droneload.vision.calibrate`.

- [ ] **Decide where real camera calibration files are kept.** `camera.yaml` is
  gitignored for now. Each camera needs its own file.

- [ ] **Use marker positions in the detection loop.** This may change the CSV
  format, which needs a person's decision.

- [ ] **Measure vibration in flight.** `testing/vibration_test.py` is simulated.
  Record markers from a flying drone, and set a fixed short exposure on live
  cameras. Only `camera_picamera2.py` sets exposure today.

- [x] **Tracker drops shaken markers.** The fixed 40 px move limit is now
  0.75 marker sides (at least 20 px). On fdcl-gwu at moderate shake, tracked
  rose from 33% to 54% with no more false IDs.

- [ ] **Confirming costs recall under shake.** At moderate shake the detector
  finds 64% of markers and the tracker reports 54%, even with no move limit,
  because a marker needs 3 hits in 5 frames. Try re-running `detectMarkers` on
  an upscaled crop around each track's last position when it is missed.
  The 3-of-5 rule is kept for now (see `logs/DECISIONS.md`).

- [ ] **To consider: keep confirmed markers through short gaps.** Under shake
  the detector finds each marker in bursts (3.4 frames on average). At fdcl-gwu
  moderate, 12.8% of detections are dropped because a marker already reported
  has fewer than 3 hits in its last 5 frames; the move limit drops only 0.5%.
  Prototype: still need 3 of 5 for the first report, then keep reporting until
  the track is deleted (5 frames without a hit), as DeepSORT does.

  | | Now | Prototype |
  |---|---|---|
  | fdcl-gwu moderate tracked (raw 63.8%) | 54.1% | 60.2% |
  | fdcl-gwu moderate false IDs/100 frames | 0.1 | 0.1 |
  | Shadow-ArUco moderate tracked (raw 61.0%) | 53.8% | 56.8% |
  | Shadow-ArUco clean false IDs/100 frames | 3.7 | 4.6 |
  | `benchmark --track` found / unmatched | 53.2% / 2.4% | 54.1% / 2.8% |

  Cost: a wrong ID near a confirmed marker is reported after one hit. Not
  adopted on 2026-11-16 because 3 of 5 is preferred; revisit with flight
  footage.

- [x] **Decide the tracker's smoothing weight (plan Task 3).** Set to 1.0 on 2026-11-16. The smoothing
  study (`analysis/smoothing/`) finds that `SMOOTHING = 0.6` leaves logged
  positions 15.2 px behind the marker at fdcl-gwu moderate shake, against
  1.7 px at 1.0, with recall and false IDs unchanged. On a still scene it does
  steady the estimate (Shadow-ArUco: −14%). Needs the project lead.

- [x] **Update the shake baseline in `AGENTS.md` and `DECISIONS.md`.** Both
  still say moderate `tracked=32.6%`; since the size-scaled gate it is 54.1%.

- [ ] **Retest camera-motion compensation on flight footage.** A KLT +
  `estimateAffinePartial2D` prototype gave no gain on the simulated (global
  affine) shake, added false IDs and cost 5.7 ms per frame on a PC. Real
  wobble and parallax may change that.

- [ ] **`DICT_4X4_50` corrects no bit errors.** OpenCV allows
  `int(1 × errorCorrectionRate)` bits, so the default 0.6 gives 0: one bit
  flipped by blur rejects the marker (checked on OpenCV 4.10). `1.0` enables
  1-bit correction but adds false positives; drop IDs outside 0-9 with it.
  Needs a `DICT_4X4_50` shake set to judge, since neither baseline uses it.

- [ ] **`--show` fails on Wayland.** The pip OpenCV wheel has no Qt Wayland
  plugin, so the window does not open. `QT_QPA_PLATFORM=xcb` works through
  XWayland. Consider setting it in `detect.py` or noting it in the README.

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

- [ ] **Fix the bugs from the 2026-11-16 review.** The benchmark skips the
  size filter, the loop sleeps 10 ms per frame, video files are timed by the
  wall clock, `--record` is always 30 fps, a dead camera warns forever and a
  bad `--dict` leaks the camera. Plan: `docs/plans/2026-11-16-review-fixes.md`.

- [ ] **`flight` never reads `COMMAND_ACK`.** A rejected arm or takeoff shows
  only as a timeout, with no reason. Needs a person's OK, as it is flight
  controller code.

- [ ] **`camera_picamera2.py` may swap red and blue (unverified).** Picamera2
  documents `RGB888` as already in BGR order, so the `RGB2BGR` conversion
  would be wrong and wasted. Grey ArUco detection barely notices; posters and
  path colours would. Check on a Raspberry Pi.

- [ ] **Skip the colour conversion on the board (unverified).** The CSI
  pipeline converts NV12 to BGR on the CPU, then the loop converts BGR to
  grey. The NV12 Y plane is already the grey image. Measure on the board.

- [ ] **Set MJPG and a buffer of one frame for USB cameras (unverified).**
  `OpenCVCamera` sets neither. Many UVC cameras give 720p at about 10 fps
  without MJPG, and queued frames arrive late. Check on the chosen camera.

- [ ] **`--show` plays video files faster than real time.** Without the per-frame sleep only `waitKey(1)` paces the window. If wanted, wait out the frame period when `--show` is on and the source is a file. `--record` already keeps the right speed.

- [ ] **README flight-demo sentence differs between languages.** `README.md:157` says "on simulated optical flow without GPS"; `README.fr.md:157` leaves it out.

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
