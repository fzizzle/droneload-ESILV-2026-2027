# Flight Velocity Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK before any task starts:** this is code that commands a drone (`AGENTS.md`, Stop and Ask). It stays simulator-only: `is_simulator()` is not touched.

**Goal:** Give `Vehicle` what a camera-driven controller needs: velocity commands, the drone's attitude, height and battery, and calls that return at once so vision can run between them.

**Architecture:** Today every `Vehicle` method blocks inside `_wait()`, which is also the only place heartbeats are sent. This plan adds `poll()`, which sends a heartbeat if one is due and reads waiting messages without blocking, and `request_*` methods that send a command and return. The blocking methods stay and are rebuilt on top of them, so the demo and its tests keep working. The heartbeat stays tied to the caller's loop on purpose: if the mission hangs, heartbeats stop and ArduPilot lands.

**Tech Stack:** `pymavlink`, pytest. No new dependency.

**Spec:** `docs/plans/2026-11-18-roadmap.md`, "Shared Interfaces". MAVLink details from ArduPilot's "Copter commands in Guided mode" page (read 2026-11-18).

## Global Constraints

- `is_simulator()` and the refusal in `main()` do not change.
- Velocity is sent with `SET_POSITION_TARGET_LOCAL_NED`, frame `MAV_FRAME_BODY_OFFSET_NED`, type mask `0b010111000111` (1479: velocity and yaw rate). In that frame ArduPilot reads velocity as forward, right, down relative to the drone's heading.
- ArduPilot stops the drone 3 s after the last velocity command. Callers resend every tick; this plan adds no keep-alive of its own.
- New limits, as constants at the top of `vehicle.py`: `MAX_SPEED_MPS = 0.5`, `MAX_CLIMB_MPS = 0.3`, `MAX_YAW_RATE_RPS = 0.5`. `send_velocity` clamps to them.
- Stream rates: `ATTITUDE` 20 Hz, `DISTANCE_SENSOR` 10 Hz, `SYS_STATUS` 1 Hz, `LOCAL_POSITION_NED` 10 Hz as now.
- `PilotTakeover` keeps its meaning: any mode change this program did not ask for.
- Existing tests in `tests/test_flight.py` and `tests/test_flight_sitl.py` pass unchanged, apart from Task 4's fix.
- Branch `feature/flight-velocity`, log `logs/YYYY-MM-DD-feature-flight-velocity.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`. Run `DRONELOAD_SITL=1 python -m pytest tests/test_flight_sitl.py` at the end of every task.

## Review Focus

1. **`poll()` called with no messages waiting:** it must return at once, not wait `RECV_TIMEOUT_S`. Test `test_poll_does_not_block` (Task 1).
2. **A velocity above the limit, or NaN:** clamped, and NaN sends zero. Test `test_velocity_is_clamped` and `test_nan_velocity_sends_zero` (Task 2).
3. **`send_velocity` outside Guided or while disarmed:** it sends nothing and raises nothing, so a controller that runs one tick late cannot fight the pilot. Test `test_no_velocity_outside_guided` (Task 2).
4. **A rejected command:** `COMMAND_ACK` with a result other than accepted or in progress raises `CommandRejected` with the command's name and the result's name. Test `test_rejected_command_raises` (Task 3).
5. **A rangefinder reading from a sensor that does not point down:** ignored. Test `test_height_ignores_other_orientations` (Task 3).

---

### Task 1: `poll()` and non-blocking requests

**Files:**
- Modify: `droneload/flight/vehicle.py`
- Test: `tests/test_flight.py`

**Interfaces:**
- Produces:

```python
vehicle.poll() -> None            # heartbeat if due; read every waiting message; never blocks
vehicle.request_mode(mode) -> None       # sends; expected_mode is set when a heartbeat shows the mode
vehicle.request_arm() -> None            # checks FAILSAFE_PARAM as arm() does, then sends once
vehicle.request_takeoff(alt_m) -> None
```

`set_mode()`, `arm()` and `takeoff()` keep their behaviour and call the `request_*` methods.

- [ ] **Step 1: Write the failing tests,** using `FakeMaster`. Extend its `recv_match` to record the `blocking` argument.

  - `test_poll_reads_all_waiting_messages`: three queued messages (heartbeat, position, heartbeat) are all applied by one `poll()`: `mode`, `armed` and `position` are set.
  - `test_poll_does_not_block`: with an empty queue, every `recv_match` call made by `poll()` had `blocking=False`.
  - `test_poll_sends_heartbeats_on_time`: two `poll()` calls 0.1 s apart send one heartbeat; a third after `HEARTBEAT_PERIOD_S` sends a second.
  - `test_poll_raises_on_takeover`: after `request_mode("GUIDED")` is confirmed by a heartbeat, a heartbeat in `LOITER` makes `poll()` raise `PilotTakeover`.
  - `test_request_mode_is_not_a_takeover`: between `request_mode("LAND")` and the heartbeat that confirms it, a heartbeat still in `GUIDED` raises nothing.
  - `test_request_arm_refuses_without_failsafe`: with `FS_GCS_ENABLE = 0`, `request_arm()` raises `FailsafeOff` and sends no arm command.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_flight.py -q -k "poll or request"`.
- [ ] **Step 3: Implement.** `request_mode` stores a pending mode; `_update` moves it to `expected_mode` when a heartbeat matches.
- [ ] **Step 4: Run the whole file, then the simulator tests.** Expected: all pass.
- [ ] **Step 5: Commit.** Message "Add Vehicle.poll and non-blocking requests".

### Task 2: Velocity commands

**Files:**
- Modify: `droneload/flight/vehicle.py`
- Test: `tests/test_flight.py`, `tests/test_flight_sitl.py`

**Interfaces:**
- Produces: `vehicle.send_velocity(forward_mps, right_mps, down_mps=0.0, yaw_rate_rps=0.0) -> None` and `vehicle.stop() -> None`.

- [ ] **Step 1: Write the failing tests.**

  - `test_velocity_message`: `send_velocity(0.2, -0.1, 0.05, 0.3)` in Guided and armed sends one `set_position_target_local_ned` with frame `MAV_FRAME_BODY_OFFSET_NED`, mask 1479, velocities `(0.2, -0.1, 0.05)` and yaw rate `0.3`.
  - `test_velocity_is_clamped`: `send_velocity(5, -5, 5, 5)` sends `(0.5, -0.5, 0.3)` and yaw rate `0.5`. The horizontal clamp scales both axes together, so `send_velocity(1, 1)` sends a vector of length 0.5 at 45°.
  - `test_nan_velocity_sends_zero`: `send_velocity(float("nan"), 0)` sends zeros.
  - `test_no_velocity_outside_guided`: in `LOITER`, or disarmed, nothing is sent.
  - `test_stop_sends_zero`.
  - Simulator, in `tests/test_flight_sitl.py`: `test_velocity_moves_the_drone`: after take-off, sending `(0.3, 0)` every 0.1 s for 4 simulated seconds moves the drone 0.8 to 1.6 m north of its start and under 0.2 m sideways. `test_velocity_stops_when_commands_stop`: 5 simulated seconds after the last command, horizontal speed is under 0.05 m/s.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the unit and simulator tests.**
- [ ] **Step 5: Commit.** Message "Add body-frame velocity commands".

### Task 3: Telemetry and command results

**Files:**
- Modify: `droneload/flight/vehicle.py`
- Test: `tests/test_flight.py`
- Docs: `TODO.md` ("`flight` never reads `COMMAND_ACK`")

**Interfaces:**
- Produces: `vehicle.attitude` (`(roll, pitch, yaw)` in radians from `ATTITUDE`), `vehicle.height_m` (from `DISTANCE_SENSOR` with orientation `MAV_SENSOR_ROTATION_PITCH_270`, centimetres converted to metres), `vehicle.battery` (`(volts, percent)` from `SYS_STATUS`; percent is `None` when the autopilot reports −1), each `None` until first received. `class CommandRejected(Exception)`. `request_position_stream()` becomes `request_streams()` and asks for all four streams.

- [ ] **Step 1: Write the failing tests.** `test_attitude_is_read`, `test_height_is_read` (a 152 cm reading gives 1.52), `test_height_ignores_other_orientations`, `test_battery_is_read` (11 800 mV and 64% give `(11.8, 64)`), `test_battery_percent_unknown`, `test_rejected_command_raises` (an ack for `MAV_CMD_NAV_TAKEOFF` with `MAV_RESULT_DENIED` raises `CommandRejected` whose text contains `NAV_TAKEOFF` and `DENIED`), `test_accepted_command_is_quiet`, and `test_streams_are_requested` (four `SET_MESSAGE_INTERVAL` commands with intervals 50 000, 100 000, 1 000 000 and 100 000 µs).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement** in `_update`. The arm retry loop in `arm()` must treat a rejected arm as "not ready yet" and keep its timeout, as it does now.
- [ ] **Step 4: Run the unit and simulator tests.**
- [ ] **Step 5: Tick the `TODO.md` item and commit.** Message "Read attitude, height, battery and command results".

### Task 4: Make `move()` check arrival

`move()` passes when the drone has travelled the right distance in any direction. With the heading known, it can check the right place.

**Files:**
- Modify: `droneload/flight/vehicle.py:143-153`
- Test: `tests/test_flight.py`

- [ ] **Step 1: Write the failing test.** `test_move_needs_the_right_direction`: after `move(1.0)` with yaw 0, positions that go 1 m east never finish and raise `FlightTimeout`; positions that go 1 m north finish.
- [ ] **Step 2: Run it and check it fails.**
- [ ] **Step 3: Implement.** The target is `start + rotate((forward_m, right_m), yaw)`; done when within `MOVE_TOLERANCE_M` of it. `move()` waits for `attitude` as it waits for `position`.
- [ ] **Step 4: Run the unit and simulator tests.** Update the existing move tests' fake messages to include an `ATTITUDE` message.
- [ ] **Step 5: Commit.** Message "Check that move() arrives at its target".

### Task 5: A fake vehicle for other modules' tests

**Files:**
- Create: `testing/fake_vehicle.py`
- Test: `tests/test_fake_vehicle.py`
- Docs: `droneload/flight/README.md` (Status and a short "For other modules" section), `README.md` and `README.fr.md` (Project Structure), `docs/mission-map.md` (statuses)

**Interfaces:**
- Produces:

```python
class KinematicVehicle:
    """Same surface as flight.Vehicle. Integrates velocity commands; no MAVLink."""
    def __init__(self, north=0.0, east=0.0, yaw=0.0, response_s=0.5, drift_mps=(0.0, 0.0)): ...
    mode, armed, position, attitude, height_m, battery     # as Vehicle
    def poll(self); def request_mode(self, mode); def request_arm(self); def request_takeoff(self, alt_m)
    def send_velocity(self, forward_mps, right_mps, down_mps=0.0, yaw_rate_rps=0.0); def stop(self)
    def step(self, dt) -> None      # advance time
    def take_over(self) -> None     # the next poll() raises flight.PilotTakeover
```

Velocity follows the command with a first-order lag of `response_s`. Roll and pitch follow the horizontal acceleration (`pitch = −a_forward / 9.81`, `roll = a_right / 9.81`), so tilt compensation is exercised. The last command expires after 3 s. `request_takeoff` climbs at `MAX_CLIMB_MPS` to the height; mode `LAND` descends and disarms at the floor.

- [ ] **Step 1: Write the failing tests.** `test_velocity_integrates` (0.3 m/s forward for 10 s at yaw 0 ends 2.7 to 3.0 m north), `test_velocity_follows_heading` (at yaw π/2 the same command moves east), `test_command_expires` (speed is zero 3.5 s after the last command), `test_tilts_when_accelerating` (pitch is negative during the first 0.2 s of a forward command and near zero after 5 s), `test_takeoff_and_land` (take-off to 1.5 m, then `LAND` ends with `armed` false and height 0), `test_take_over_raises`, and `test_limits_match_vehicle` (commands above `flight.MAX_SPEED_MPS` are clamped the same way).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and the simulator tests.**
- [ ] **Step 5: Update the docs listed above and commit.** Message "Add a kinematic fake vehicle for tests".

## Done When

- [ ] A loop of `poll()`, `send_velocity()` and `sleep(0.05)` flies the simulator.
- [ ] `./scripts/check.sh` and the simulator tests pass, docs are updated and the pull request is open.

## Not in This Plan

- Connecting to a real drone. See Stage 6 of `docs/plans/2026-11-18-kit-bring-up.md`.
- Relay output for the grabber (`docs/plans/2026-11-18-payload.md`) and `LANDING_TARGET` (`docs/plans/2026-11-18-precision-landing.md`).
