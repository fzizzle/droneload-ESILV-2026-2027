# Mission Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a mission as a list of steps at a fixed rate, with a timeout on every step and a landing whenever one fails, so that later plans only have to write steps.

**Architecture:** One loop at 20 Hz owns the vehicle. Each tick it calls `vehicle.poll()`, reads the newest frame from each camera, runs detection, and ticks the current step. Because the loop is the only caller of `poll()`, a hung mission stops the heartbeats and ArduPilot lands the drone. A step is any object with `name`, `timeout_s`, `start(ctx)` and `tick(ctx)`; the runner knows nothing about what steps do.

**Tech Stack:** Standard library, pytest. No new dependency. Tests use `testing.fake_vehicle.KinematicVehicle`.

**Spec:** `docs/plans/2026-11-18-roadmap.md`, "Shared Interfaces"; `droneload/mission/README.md`, Requirements and Done When.

## Global Constraints

- `TICK_HZ = 20`, a constant at the top of `runner.py`.
- **The operator may only confirm that an action has finished** (rules, Flight Test). The runner has one input: confirm. It has no way to choose a target, skip a step or steer.
- A pilot takeover ends the mission at once and sends nothing more. It is not a failure to recover from.
- Every other failure, a timeout and Ctrl+C all run the abort steps, which default to landing.
- Each state change is logged with its time, step name and reason.
- `mission` imports the other modules; none of them imports `mission`.
- Needs `docs/plans/2026-11-18-flight-velocity.md` merged. Flying it in the simulator (Task 3) commands a simulated drone and needs the project lead's OK.
- Branch `feature/mission-runner`, log `logs/YYYY-MM-DD-feature-mission-runner.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **A step that raises an unexpected exception:** treated as a failure, so the abort steps run and the drone lands; the exception text goes in the log. Test `test_exception_aborts_to_landing` (Task 1).
2. **An abort step that itself fails or times out:** the runner stops commanding and returns `"aborted"`; it does not loop. ArduPilot's failsafe is then the way down. Test `test_failed_abort_ends_the_run` (Task 1).
3. **A tick that overruns 50 ms:** the loop does not sleep, does not try to catch up, and logs a warning once per second at most. Test `test_slow_tick_does_not_spiral` (Task 1).
4. **Low battery:** below `MIN_BATTERY_PERCENT = 25` the run aborts to landing between steps or mid-step. Test `test_low_battery_aborts` (Task 2).
5. **A camera that returns no new frame this tick:** `ctx.markers[name]` keeps its last value, and `ctx.frame_age_s[name]` grows, so a step can tell old data from new. Test `test_stale_frame_is_marked` (Task 1).

---

### Task 1: The runner

**Files:**
- Create: `droneload/mission/__init__.py`, `droneload/mission/runner.py`
- Test: `tests/test_mission.py`

**Interfaces:**
- Consumes: `Vehicle.poll()`, `flight.PilotTakeover`, `MarkerDetector.process()`.
- Produces: `Context` and `run()` as in the roadmap, with one field added: `frame_age_s: dict`, seconds since each camera's last new frame. `run(steps, ctx, abort=None, clock=time.monotonic, sleep=time.sleep, log=print) -> str`.

- [ ] **Step 1: Write the failing tests.** Use scripted steps (a small test class whose `tick` returns values from a list) and a fake clock.

  - `test_steps_run_in_order`: three steps that finish after 2, 1 and 3 ticks give `"complete"`, with `start` called once each, in order.
  - `test_step_timeout_aborts`: a step that never finishes, with `timeout_s = 1`, ends after 20 ticks; the abort step runs; the result is `"aborted"`.
  - `test_failed_step_aborts`: `tick` returning `False` runs the abort steps.
  - `test_exception_aborts_to_landing`, `test_failed_abort_ends_the_run`, `test_slow_tick_does_not_spiral`, `test_stale_frame_is_marked`: as in Review Focus.
  - `test_pilot_takeover_stops_everything`: when `poll()` raises `PilotTakeover`, the result is `"pilot"`, no abort step starts, and no call reaches the vehicle afterwards.
  - `test_poll_every_tick`: `poll()` is called once per tick, before the step.
  - `test_vision_runs_every_tick`: a fake camera and detector are read and processed each tick, and the step sees the result in `ctx.markers["down"]` in the same tick.
  - `test_state_changes_are_logged`: the log holds one line per step start, finish, failure and abort, each with the step's name.
  - `test_keyboard_interrupt_aborts`: `KeyboardInterrupt` raised in a step runs the abort steps and returns `"aborted"`.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_mission.py -q`.
- [ ] **Step 3: Implement `Context` and `run()`.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Add the mission runner".

### Task 2: Basic steps and the confirm input

**Files:**
- Create: `droneload/mission/steps.py`
- Modify: `droneload/mission/runner.py` (battery check, confirm input)
- Test: `tests/test_mission.py`

**Interfaces:**
- Consumes: `request_mode`, `request_arm`, `request_takeoff`, `send_velocity`, `stop`, `position`, `armed`, `battery`.
- Produces, in `steps.py`:

```python
Arm(timeout_s=60)                      # Guided, then arm; re-requests every ARM_RETRY_S
TakeOff(height_m, timeout_s=30)        # done within 0.1 m of the height
Hover(seconds, timeout_s=None)         # sends zero velocity each tick; timeout defaults to seconds + 5
Land(timeout_s=60)                     # LAND mode; done when disarmed
WaitConfirm(timeout_s=120)             # hovers until ctx.confirmed
```

`run()` gains `confirm=None`, a function returning `True` once when the operator has pressed the confirm key; the runner copies it to `ctx.confirmed` each tick. `abort` defaults to `[Land()]`.

- [ ] **Step 1: Write the failing tests,** each running `run()` with a `KinematicVehicle` and a fake clock that also calls `vehicle.step(dt)`.

  - `test_take_off_hover_land`: `[Arm(), TakeOff(1.5), Hover(5), Land()]` returns `"complete"`; the height was within 0.1 m of 1.5 during the hover; the vehicle ends disarmed at height 0.
  - `test_hover_holds_against_drift`: with `drift_mps=(0.05, 0)`, `Hover(5)` still completes. Holding position is the flight controller's job; the step only sends zero velocity.
  - `test_wait_confirm`: the step finishes on the tick `confirm()` first returns `True`, and not before.
  - `test_confirm_cannot_skip_a_step`: `confirm()` returning `True` during `Hover` does not end it.
  - `test_low_battery_aborts`: a battery of 20% during `Hover(60)` aborts to `Land`.
  - `test_unknown_battery_does_not_abort`: a battery of `None`, or a percent of `None`, does not abort.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh`.**
- [ ] **Step 5: Commit.** Message "Add arm, take-off, hover, land and confirm steps".

### Task 3: Command line and a simulator run

**Files:**
- Create: `droneload/mission/__main__.py`, `droneload/mission/plans.py`
- Test: `tests/test_mission.py`, `tests/test_mission_sitl.py`
- Docs: `droneload/mission/README.md` (Status, Run it), `README.md` and `README.fr.md` (Status, Usage, Project Structure), `docs/architecture.md` (state column), `docs/mission-map.md` (statuses), `TODO.md` ("`mission` state machine")

**Interfaces:**
- Produces: `plans.PLANS`, a dict from name to a function returning a step list; the first entry is `"hover": [Arm(), TakeOff(1.5), Hover(5), Land()]`. Later plans add entries. Command line: `python -m droneload.mission --plan hover --connect tcp:127.0.0.1:5760 [--source-down SOURCE]`. It refuses a non-simulator address exactly as `droneload.flight` does, by calling `flight.vehicle.is_simulator`. The confirm key is Enter on standard input.

- [ ] **Step 1: Write the failing tests.** `test_unknown_plan_is_refused` (exit with the list of plans), `test_real_address_is_refused`, and, opt-in with `DRONELOAD_SITL=1`, `test_hover_plan_in_the_simulator` (the plan returns `"complete"`, and the drone was above 1.3 m for at least 4 simulated seconds).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and `DRONELOAD_SITL=1 python -m pytest tests/test_mission_sitl.py`.**
- [ ] **Step 5: Update the docs listed above and commit.** Message "Add the mission command line and a hover plan".

## Done When

- [ ] `python -m droneload.mission --plan hover` takes off, hovers and lands in the simulator, and prints each state change.
- [ ] Killing the program in mid-flight lands the simulated drone within 3 s, by the existing failsafe.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## Not in This Plan

- How the drone learns the referee's target. It is an open question for the organisers; steps read it from `ctx.notes["target"]`, and `docs/plans/2026-11-18-poster-recognition.md` says what sets it.
- The jury display and the flight recorder. Each has its own plan and hooks into the runner's tick.
