# Centre and Land on a Marker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK before Task 2:** from there on, this code steers a simulated drone (`AGENTS.md`, Stop and Ask).

**Goal:** Hold the drone over a marker seen by the downward camera, and land on ArUco 0 within 10 cm. Centring is the base of the landing, the drop, the hover in zone C and following the robot.

**Architecture:** `vision` gives the marker's position in the camera frame. `navigation/frames.py` turns it into forward and right distances on the floor, removing the drone's tilt. `navigation/centre.py` turns those into a velocity with a clamped proportional controller. Two steps use it: one centres, the other centres while descending and hands over to ArduPilot's Land mode near the floor, where the marker no longer fits in the image.

**Tech Stack:** numpy, pytest. No new dependency. Tests use `testing.sim_camera` and `testing.fake_vehicle`.

**Spec:** `docs/plans/2026-11-18-roadmap.md`, "Shared Interfaces"; `droneload/navigation/README.md`, Requirements ("Landing on the take-off marker: within 10 cm, 9 times in 10") and Design Notes.

## Global Constraints

- Needs these plans merged: `sim-camera`, `vision-api`, `flight-velocity`, `mission-runner`.
- Settings are constants at the top of `droneload/navigation/centre.py`:
  `CENTRE_GAIN = 0.8` (1/s), `CENTRE_MAX_SPEED_MPS = 0.3`, `CENTRE_TOLERANCE_M = 0.05`, `CENTRE_HOLD_S = 1.0`, `LOST_AFTER_S = 1.0`, `DESCENT_MPS = 0.2`, `HANDOVER_HEIGHT_M = 0.4`, `MAX_FRAME_AGE_S = 0.2`.
- `navigation` may import `vision` and `flight`. It does not import `mission`; its steps follow the step shape by convention.
- Any filtering of a target's position happens here, not in `vision` (`logs/DECISIONS.md`, 2026-11-16).
- ArduPilot holds position. These controllers only send velocities, and send zero when unsure.
- Branch `feature/centre-and-land`, log `logs/YYYY-MM-DD-feature-centre-and-land.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Marker lost mid-centring:** zero velocity at once; after `LOST_AFTER_S` the step fails, so the runner lands. It never flies on the last known position. Test `test_lost_marker_fails_the_step` (Task 2).
2. **Stale frame:** a frame older than `MAX_FRAME_AGE_S` counts as no detection. Test `test_stale_frame_counts_as_lost` (Task 2).
3. **Tilt:** while the drone pitches to move, the marker shifts in the image. Without tilt removal the controller oscillates. Test `test_tilt_is_removed` (Task 1) and `test_centres_while_tilting` (Task 2).
4. **A marker with no `offset_m`** (no calibration loaded): the step fails at `start` with a message naming the missing calibration, rather than at the first tick. Test `test_missing_calibration_fails_at_start` (Task 2).
5. **Marker lost below the handover height:** expected, since it no longer fits the image; the landing continues. **Lost above it:** the descent stops and the step fails. Test `test_marker_lost_high_stops_the_descent` (Task 3).

---

### Task 1: Frame conversion

**Files:**
- Create: `droneload/navigation/__init__.py`, `droneload/navigation/frames.py`
- Test: `tests/test_navigation.py`

**Interfaces:**
- Produces:

```python
DOWN_CAMERA    = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])   # camera to body: top of image is the drone's front
FORWARD_CAMERA = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])    # camera to body: lens along the drone's nose

def level_offset(offset_cam, mount, roll, pitch) -> tuple   # (forward_m, right_m, down_m)
```

`level_offset` rotates a camera-frame point into the body frame with `mount`, then removes roll and pitch (`Ry(pitch) @ Rx(roll) @ body`), leaving yaw alone.

- [ ] **Step 1: Write the failing tests.**

  - `test_down_camera_axes`: with no tilt, `(0, -0.3, 1.5)` (the marker is 0.3 m up the image) gives `(0.3, 0.0, 1.5)`, and `(0.2, 0, 1.5)` gives `(0.0, 0.2, 1.5)`.
  - `test_forward_camera_axes`: `(0.2, -0.1, 3.0)` gives `(3.0, 0.2, -0.1)`.
  - `test_tilt_is_removed`: render a marker with `sim_camera.render_down` from directly above at 1.5 m with `roll = radians(8)` and `pitch = radians(-5)`; detect it, take `pose.marker_offset`, and check `level_offset(..., roll, pitch)` gives forward and right within 2 cm of 0 and down within 3 cm of 1.5.
  - `test_tilt_with_an_offset`: the same from 0.3 m south and 0.2 m west of the marker gives `(0.3, 0.2, 1.5)` within 3 cm.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_navigation.py -q`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Convert camera offsets to level forward and right distances".

### Task 2: Centring

**Files:**
- Create: `droneload/navigation/centre.py`
- Test: `tests/test_navigation.py`

**Interfaces:**
- Consumes: `level_offset`, `Context` fields `vehicle`, `markers`, `frame_age_s`, `now_s`.
- Produces:

```python
class Centring:
    def __init__(self, gain=CENTRE_GAIN, max_speed=CENTRE_MAX_SPEED_MPS,
                 tolerance_m=CENTRE_TOLERANCE_M, hold_s=CENTRE_HOLD_S): ...
    def update(self, offset, now_s) -> tuple   # offset: (forward_m, right_m) or None; returns (forward_mps, right_mps)
    def centred(self) -> bool                  # within tolerance for hold_s without a break
    def lost(self, now_s) -> bool              # no offset for LOST_AFTER_S

def marker_offset_level(ctx, marker_id, camera="down") -> tuple | None
#   the marker's (forward_m, right_m, down_m) this tick, or None if absent, stale or without offset_m

class CentreOnMarker:                          # a step
    def __init__(self, marker_id, camera="down", timeout_s=30): ...
```

`update` returns `gain × offset`, with its length clamped to `max_speed`, and `(0, 0)` for `None`.

- [ ] **Step 1: Write the failing tests.** Unit tests on `Centring` first:

  - `test_velocity_points_at_the_target`: `(0.1, -0.05)` gives `(0.08, -0.04)`.
  - `test_velocity_is_clamped`: `(2, 0)` gives `(0.3, 0)`; `(2, 2)` gives a vector of length 0.3.
  - `test_no_target_means_stop`: `None` gives `(0, 0)`.
  - `test_centred_needs_the_hold_time`: inside tolerance for 0.9 s is not centred; for 1.0 s it is; one sample outside resets the clock.
  - `test_lost_after_a_second`.

  Then closed loop, with `KinematicVehicle`, a `SimCamera` over `make_floor({0: (4.0, 2.5)})` and the mission runner:

  - `test_centres_over_the_marker`: from 0.4 m north-east of the marker at 1.5 m, `CentreOnMarker(0)` finishes within 15 s, with the vehicle within 5 cm of `(4.0, 2.5)`.
  - `test_centres_while_tilting`: the same with `response_s=0.3`, so the fake tilts hard; it finishes, and the distance to the marker never grows for more than 0.5 s once it has started closing.
  - `test_holds_against_drift`: with `drift_mps=(0.05, 0.02)`, the vehicle stays within 10 cm for 10 s after centring.
  - `test_lost_marker_fails_the_step`, `test_stale_frame_counts_as_lost`, `test_missing_calibration_fails_at_start`: as in Review Focus.
  - `test_other_markers_are_ignored`: with markers 0 and 4 in view, `CentreOnMarker(0)` ends over 0.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Centre over a marker with the downward camera".

### Task 3: Landing on a marker

**Files:**
- Modify: `droneload/navigation/centre.py`, `droneload/mission/plans.py`
- Test: `tests/test_navigation.py`, `tests/test_mission_sitl.py`
- Docs: `droneload/navigation/README.md` (Status, measured results), `docs/mission-map.md` (statuses), `README.md` and `README.fr.md` (Status), `TODO.md` ("`navigation` in the simulator")

**Interfaces:**
- Produces: `class LandOnMarker` (a step): `LandOnMarker(marker_id=0, camera="down", timeout_s=60)`. Phases: centre at the current height; descend at `DESCENT_MPS` while centring; below `HANDOVER_HEIGHT_M` (from `vehicle.height_m`, or `-position[2]` when that is `None`) request `LAND`; done when disarmed. New plan `"pad"` in `plans.PLANS`: `[Arm(), TakeOff(1.5), CentreOnMarker(0), Hover(3), LandOnMarker(0)]`.

- [ ] **Step 1: Write the failing tests.**

  - `test_lands_on_the_marker`: from 0.4 m off at 1.5 m, the vehicle ends disarmed within 10 cm of the marker.
  - `test_landing_repeats`: 10 runs from start points on a 0.5 m circle, with `drift_mps` of 0.05 m/s in a different direction each run, all end within 10 cm.
  - `test_descent_waits_for_centring`: the height does not drop below 1.4 m until the first time the vehicle is within `CENTRE_TOLERANCE_M`.
  - `test_marker_lost_high_stops_the_descent`: removing the marker from the floor at 1.0 m fails the step, with zero velocity sent first.
  - `test_marker_lost_low_still_lands`: the marker leaving the image below 0.4 m does not fail the step.
  - Opt-in simulator test `test_pad_plan_in_the_simulator`: the `"pad"` plan, with a `SimCamera` fed by `sim_camera.vehicle_pose`, returns `"complete"` and the final position is within 15 cm of the marker.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and the simulator tests.** Note the simulator's landing error in the log and in the `navigation` README.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Land on a marker".

## Done When

- [ ] The `"pad"` plan lands within 15 cm of ArUco 0 in the ArduPilot simulator, 5 runs in 5.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- Measure the landing error on the drone, 10 landings. If fewer than 9 are within 10 cm, see `docs/plans/2026-11-18-precision-landing.md`.
- Take-off and landing on ArUco 0 are conditions of both round-trip scores (30 and 70 points).
