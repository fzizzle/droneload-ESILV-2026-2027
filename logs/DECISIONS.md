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
