# Decisions

Lasting decisions, one line each. Keep this file short.

- 2026-10-30: Assume the loan kit for the drone. Companion computer and cameras are undecided, so sources are chosen with `--source` through `cv2.VideoCapture`.
- 2026-10-30: `DICT_4X4_50` stays the default dictionary; `--dict` exists for test footage.
- 2026-10-30: `AGENTS.md` is the single rules file; `CLAUDE.md` only imports it.
- 2026-10-30: `ruff` lints but does not format, because `detect.py` uses aligned assignments.
- 2026-10-30: Rules are pinned in `ruff.toml` so every contributor gets the same result.
- 2026-10-30: Expensive checks run in CI, because CI costs agents no tokens.
- 2026-10-31: `ARUCO_LABELS` follows the V0 rules: IDs 0-9, with `fenetre_recto_*` and `fenetre_verso_*`.
- 2026-10-31: Stabilisation sits inside `flight`, and ArduPilot does it, not companion computer code.
- 2026-10-31: Focus on the organisers' Qualcomm companion computer, model unconfirmed. The team buys the cameras.
- 2026-10-31: Proposed: global-shutter cameras with fixed short exposure, because simulated wobble hurts detection more than blur.
- 2026-10-31: `vision/tracking` keeps detections steady; `flight/stabilisation` holds flight stability. Whole-image stabilisation is a last resort.
- 2026-11-04: `flight` uses `pymavlink` with ArduPilot; DroneKit is unmaintained and MAVSDK targets PX4.
- 2026-11-04: The simulator is ArduPilot's prebuilt SITL binary, pinned to Copter 4.7.2 with a checksum. Gazebo is not used yet.
- 2026-11-04: `flight` connects only to a local simulator until a person approves flying a drone.
- 2026-11-09: If the program stops, ArduPilot's GCS failsafe lands after 3 s without a heartbeat (`flight/failsafe.parm`), instead of Python sending zero velocity.
- 2026-11-09: The simulator flies without GPS, on optical flow and a rangefinder. Estimator settings are in `flight/stabilisation/indoor.parm`; simulated sensors are in `testing/sitl_sensors.parm`.
- 2026-10-30: Code is organised by module; see `docs/architecture.md`.
- 2026-10-30: Install instructions use a `.venv` and the `python` command, which works on Mac, Windows and Linux.
- 2026-10-30: Team 450's drone goes back to the organisers and is not reused.
- 2026-10-30: Only the main README has a French version. Other docs are in English, because a second language doubles each edit.
- 2026-11-13: With tracking on, CSV rows hold the smoothed position of confirmed markers; the columns are unchanged. Approved by the project lead.
- 2026-11-13: Detection reports a marker only after it is seen in 3 of the last 5 frames, with its position smoothed; `--no-track` turns this off.
- 2026-11-13: `requirements-dev.txt` uses the GUI `opencv-contrib-python` wheel, not the headless one, so `--show` can open a window. Approved by the project lead.
- 2026-11-13: Calibration uses a checkerboard with 9 × 6 inner corners and 25 mm squares by default, and writes OpenCV YAML with `camera_matrix`, `dist_coeffs`, `image_width`, `image_height` and `rms_px`.
- 2026-11-16: The shake baseline is `vibration_test --source` on fdcl-gwu at moderate shake (seed 1): raw 63.8%, tracked 32.6%. Saved shaken videos in `test_footage/shaken/` are for watching; scores come from the in-memory run.
- 2026-11-16: The tracker's move limit is max(20 px, 0.75 × marker side) × frames since last seen, replacing the fixed 40 px.
- 2026-11-16: For now, the 3-of-5 rule applies to keeping a marker, not only to its first report. Keeping confirmed tracks confirmed through gaps stays an option; see `TODO.md`.
- 2026-11-16: Analysis notebooks and their dependencies (`plotly`, `kaleido`, `nbformat`, `jupyter`) live in `analysis/`; CI and the drone do not install them. Notebooks are committed with outputs cleared.
- 2026-11-16: With tracking on, CSV rows hold the detected position of confirmed markers (`SMOOTHING = 1.0`), superseding the smoothed positions of 2026-11-13. Approved by the project lead after `analysis/smoothing/`.
- 2026-11-16: Any smoothing for steering (centring, landing) goes in `navigation`, with the drone's motion known, not in `vision`'s logged positions.
- 2026-11-16: The shake baseline is now raw 63.8%, tracked 54.1%, tracked err 1.7 px (size-scaled gate, no smoothing), superseding tracked 32.6%.
- 2026-11-16: The benchmark applies MIN_SIDE_PX as the app does. The baseline is now found=56.4% unmatched=10.9%, superseding unmatched=26.6%.
- 2026-11-16: For a video file, CSV timestamps and the cooldown follow the run's start time plus the frame's position in the video; live cameras keep real time. The columns are unchanged. Approved by the project lead.
- 2026-11-16: --record keeps a video file's frame rate; a live camera is recorded at 30 fps in real time, repeating or skipping frames to keep pace.
- 2026-11-16: A live camera that sends no frame for 2 s is released and reopened, then every 2 s, with one warning per attempt. Approved by the project lead.
- 2026-11-16: polygonalApproxAccuracyRate returns to OpenCV's default 0.03 (was 0.05). Baselines are now found=57.6% unmatched=4.1%, and moderate shake raw=65.9% tracked=57.2%, superseding found=56.4% unmatched=10.9% and raw=63.8% tracked=54.1%.
