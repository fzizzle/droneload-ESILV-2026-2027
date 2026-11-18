# Precision Landing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK before any task starts:** this is flight controller code and changes flight controller settings (`AGENTS.md`, Stop and Ask).

> **Start this plan only if it is needed.** `docs/plans/2026-11-18-centre-and-land.md` already lands on a marker by steering from Python and handing over to Land mode at 0.4 m. Build this if 10 landings on the drone give fewer than 9 within 10 cm.

**Goal:** Let ArduPilot itself steer the final descent onto ArUco 0, using the marker's position sent from the companion computer, so the correction continues below the height where Python has to let go.

**Architecture:** ArduPilot's precision landing takes `LANDING_TARGET` messages and steers during Land mode with its own filter, which uses the drone's motion between camera frames. Python's part shrinks to sending the marker's position each tick. This follows the project's rule that the flight controller does the stabilising (`logs/DECISIONS.md`, 2026-10-31).

**Tech Stack:** `pymavlink`, ArduPilot Copter 4.7.2 parameters. No new dependency.

**Spec:** ArduPilot's "Precision Landing and Loiter" page (read 2026-11-18); `droneload/navigation/README.md` ("within 10 cm, 9 times in 10").

## Global Constraints

- Needs `centre-and-land` merged, and Stage 1 of `docs/plans/2026-11-18-kit-bring-up.md` done: **if the Pixhawk's firmware has no `PLND_ENABLED` parameter, this plan cannot run on the kit.** Stop and record it.
- Parameters go in a new `droneload/flight/stabilisation/precland.parm`: `PLND_ENABLED = 1`, `PLND_TYPE = 1` (MAVLink), `PLND_STRICT = 1` (retry, then land), `PLND_RET_MAX = 2`, `PLND_XY_DIST_MAX = 0.3`, `PLND_ALT_MIN = 0.3`. Camera position offsets (`PLND_CAM_POS_X/Y/Z`) are measured on the drone.
- **Unverified until Task 1 proves it in the simulator:** which `LANDING_TARGET` fields Copter 4.7 uses. The plan assumes the position fields `x`, `y`, `z` in `MAV_FRAME_BODY_FRD` with `position_valid = 1`. If the simulator only accepts angles, send `angle_x = atan2(right, down)` and `angle_y = atan2(forward, down)` with `distance`; Task 1 settles which and records it.
- Only `flight` sends MAVLink. `navigation` passes it a position in the body frame.
- The Python landing from `centre-and-land` stays as the fallback, selected by one constant.
- Branch `feature/precision-landing`, log `logs/YYYY-MM-DD-feature-precision-landing.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Marker lost during the descent:** messages simply stop. ArduPilot's `PLND_STRICT = 1` then retries and lands; Python sends nothing made up. Test `test_no_marker_sends_nothing` (Task 2).
2. **Body frame, not level frame:** the message must carry the camera's measurement rotated by the mount only. Removing tilt twice makes the drone overshoot. Test `test_landing_target_is_not_tilt_corrected` (Task 2).
3. **A stale frame:** older than `MAX_FRAME_AGE_S`, it is not sent. Test `test_stale_marker_is_not_sent` (Task 2).
4. **Firmware without precision landing:** `LandOnMarker` reads `PLND_ENABLED` at `start`; when it is missing or 0 it uses the Python landing and says so on the display. Test `test_falls_back_without_precland` (Task 2).
5. **A second marker 0 in view** (a reflection, a spare print): the tracker's confirmed marker is the only one sent. Covered by `test_duplicate_id_keeps_nearest_corners` in the vision API plan; no new test.

---

### Task 1: Prove it in the simulator

**Files:**
- Modify: `droneload/flight/vehicle.py`, `scripts/sim.sh` (load `precland.parm`)
- Create: `droneload/flight/stabilisation/precland.parm`
- Test: `tests/test_flight.py`, `tests/test_flight_sitl.py`

**Interfaces:**
- Produces: `vehicle.send_landing_target(forward_m, right_m, down_m) -> None`, in the body frame.

- [ ] **Step 1: Write the failing tests.** Unit: `test_landing_target_message` (the frame, the three distances and `position_valid`). Simulator, opt-in: `test_precland_steers_the_landing`: take off to 2 m, move 0.4 m off a known point, switch to `LAND` while sending the point's body-frame position every 0.1 s computed from the simulator's own position and attitude; the drone touches down within 10 cm of the point. `test_land_without_targets_does_not_steer`: the same without messages lands within 10 cm of where it started descending, 0.4 m from the point.
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.** If the position form does not steer the simulator, switch to the angle form and adjust the unit test.
- [ ] **Step 4: Run the simulator tests 5 times.** Record in the log which message form works and the landing errors.
- [ ] **Step 5: Commit.** Message "Send landing targets to ArduPilot's precision landing".

### Task 2: Use it in `LandOnMarker`

**Files:**
- Modify: `droneload/navigation/centre.py`, `droneload/navigation/frames.py`, `testing/fake_vehicle.py`
- Test: `tests/test_navigation.py`, `tests/test_mission_sitl.py`
- Docs: `droneload/navigation/README.md` (both landing methods and their measured errors), `droneload/flight/stabilisation/README.md` (the new settings file), `logs/DECISIONS.md` (which method is the default)

**Interfaces:**
- Consumes: `send_landing_target`, `vehicle.param("PLND_ENABLED")`.
- Produces: `frames.body_offset(offset_cam, mount) -> tuple`, the mount rotation alone. `LANDING = "precland"` or `"python"`, a constant at the top of `centre.py`. With `"precland"`, `LandOnMarker` centres as before, requests `LAND` at the hover height, and sends the marker's body-frame position every tick until disarmed. `KinematicVehicle` gains `send_landing_target`, which steers its descent in `LAND` toward the last target, and a `precland` flag that tests can turn off.

- [ ] **Step 1: Write the failing tests.** `test_precland_lands_on_the_marker` (within 10 cm on the fake vehicle), `test_no_marker_sends_nothing`, `test_landing_target_is_not_tilt_corrected` (with the fake tilted 8°, the message equals `body_offset`, not `level_offset`), `test_stale_marker_is_not_sent`, `test_falls_back_without_precland`, and the opt-in `test_pad_plan_with_precland_in_the_simulator` (the `"pad"` plan ends within 10 cm of marker 0).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and the simulator tests.** Run the `"pad"` plan 5 times with each value of `LANDING` and put both sets of errors in the `navigation` README.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Land on the marker with ArduPilot's precision landing".

## Done When

- [ ] In the simulator, precision landing ends within 10 cm of the marker 5 runs in 5.
- [ ] The `navigation` README compares both methods, and `logs/DECISIONS.md` names the default.
- [ ] `./scripts/check.sh` passes and the pull request is open.

## After This Plan

- On the drone, propellers off first: load `precland.parm`, hold the drone over a marker, and check the ground station reports the target acquired.
- Then 10 landings from 1.5 m with each method, measured with a tape. Keep the better one as the default.
