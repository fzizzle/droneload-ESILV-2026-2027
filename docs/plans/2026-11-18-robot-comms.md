# Robot Communication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK:** `pyserial` is a new dependency (Task 3), the radio link is hardware beyond the loan kit (Task 3), and Task 4 steers a simulated drone.

**Goal:** Drive robot PULL-E in front of its two hidden markers, read the target it then names, and follow it from the air. This is 70 points (follow 30, robot steps 40) and the task Mission 2 needs.

**Architecture:** `comms/robot.py` is a small state machine over any byte stream: it sends `D`, `G` and `A`, and turns the robot's replies into a count of alignments and a target number. It never touches a serial port in tests. `navigation/robot.py` decides which command to send from what the downward camera sees: the robot's marker 1 and the alignment markers 2 and 3. From the air, lining the robot up with a marker is a one-dimensional problem along the rail.

**Tech Stack:** Standard library; `pyserial` for the real link only. Tests use a fake robot.

**Spec:** `docs/contest-rules.md`, Robot and Open Questions; `droneload/comms/README.md`.

## Global Constraints

- Protocol, from V1: 57600 baud, 8N1, no flow control. `D` (0x44) right, `G` (0x47) left, `A` (0x41) stop. After a stop the robot replies `N` (not aligned), `F` (first alignment) or `S` (second alignment), then a digit naming the target once both are done.
- **Two open questions are handled, not guessed:** `F` is accepted as 0x46 or 0x56, and replies are accepted whether sent 3 times or every 100 ms. Repeats within `REPEAT_WINDOW_S = 1.0` of the same stop count once.
- The robot's code is still "to be completed" in V1. Keep every protocol byte in constants at the top of `robot.py`.
- Only `comms` talks to the robot. `comms` imports no other module.
- Left and right are the robot's, on its rail. Which image direction that is depends on the drone's heading, so `navigation` learns it by watching marker 1 move after the first command.
- Electrical: the robot's 5 V pin can power an Arduino but not a Raspberry Pi, and a 3.3 V UART must not meet a 5 V one without a level converter.
- Branch `feature/robot-comms`, log `logs/YYYY-MM-DD-feature-robot-comms.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Noise bytes on the link:** anything that is not a known reply is ignored and counted, never raised. Test `test_unknown_bytes_are_ignored` (Task 1).
2. **A late reply from an earlier stop** arriving after a new move command: ignored, since replies only count while stopped. Test `test_reply_while_moving_is_ignored` (Task 1).
3. **No reply at all** (radio out of range): `Robot.silent(now_s)` turns true after `REPLY_TIMEOUT_S = 2.0`, and the guide re-sends stop, then fails the step after 3 tries. Test `test_silence_is_reported` (Task 1) and `test_guide_fails_on_silence` (Task 4).
4. **A digit outside 1 to 4,** or a digit before both alignments: ignored. Test `test_bad_target_is_ignored` (Task 1).
5. **The robot at the end of its rail:** it stops by itself. Marker 1 not moving for 1 s after a move command means "at the end", and the guide reverses. Test `test_guide_reverses_at_the_rail_end` (Task 4).

---

### Task 1: Protocol state machine

**Files:**
- Create: `droneload/comms/__init__.py`, `droneload/comms/robot.py`
- Test: `tests/test_comms.py`

**Interfaces:**
- Produces:

```python
class Robot:
    def __init__(self, link): ...       # link: any object with write(bytes) and read() -> bytes, non-blocking
    alignments: int                     # 0, 1 or 2
    target: int | None                  # 1 to 4 once known
    moving: str | None                  # "right", "left" or None
    last_reply: str | None              # "N", "F" or "S" for the latest stop
    ignored: int
    def right(self); def left(self); def stop(self)
    def poll(self, now_s) -> None       # read and interpret waiting bytes
    def silent(self, now_s) -> bool     # stopped, and no reply for REPLY_TIMEOUT_S
```

- [ ] **Step 1: Write the failing tests,** with a list-backed fake link.

  - `test_commands_send_the_right_bytes`: `right()`, `left()`, `stop()` write `b"D"`, `b"G"`, `b"A"`.
  - `test_first_alignment`: after `stop()`, the bytes `FFF` give `alignments == 1` and `last_reply == "F"`.
  - `test_f_as_0x56_is_accepted`.
  - `test_repeats_count_once`: `F` arriving 10 times over 1 s still gives `alignments == 1`.
  - `test_second_alignment_then_target`: a later stop answered `SSS` then `3` gives `alignments == 2` and `target == 3`.
  - `test_not_aligned`: `NNN` leaves `alignments` unchanged and sets `last_reply == "N"`.
  - `test_unknown_bytes_are_ignored`, `test_reply_while_moving_is_ignored`, `test_silence_is_reported`, `test_bad_target_is_ignored`: as in Review Focus.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_comms.py -q`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Add the PULL-E protocol state machine".

### Task 2: Fake robot

**Files:**
- Create: `testing/fake_robot.py`
- Test: `tests/test_comms.py`

**Interfaces:**
- Produces:

```python
class FakeRobot:
    """PULL-E on its rail, as V1 describes it. Also a link: pass it to Robot()."""
    def __init__(self, rail_m=4.0, position_m=2.0, speed_mps=0.2, align_at=(1.0, 3.2),
                 align_tolerance_m=0.05, target=3, reply_mode="three", f_byte=0x46): ...
    position_m: float
    def write(self, data); def read(self) -> bytes
    def step(self, dt) -> None
```

It moves while commanded, stops at the rail's ends, and after a stop replies `N`, `F` or `S` by its distance to the alignment points, in order: the second point only counts after the first. `reply_mode` is `"three"` or `"100ms"`.

- [ ] **Step 1: Write the failing tests.** `test_fake_moves_and_stops_at_the_end`, `test_fake_replies_by_position`, `test_fake_names_the_target_after_both`, and `test_robot_drives_the_fake` (a scripted sequence of `Robot` calls ends with `target == 3`, in both reply modes and with both `F` bytes).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Add a fake PULL-E for tests".

### Task 3: The real link

Blocked on the project lead's two decisions. Recommended: a 2.4 GHz serial bridge pair rather than the previous team's HC-12 modules, because HC-12 shares the 433 MHz band with the kit's telemetry radio. Confirm with the organisers which links the team module may use.

**Files:**
- Create: `droneload/comms/serial_link.py`
- Modify: `requirements-dev.txt` (pin `pyserial`), `README.md` and `README.fr.md` (Installation)
- Test: `tests/test_comms.py`
- Docs: `droneload/comms/README.md` (Status, the chosen link, wiring), `logs/DECISIONS.md`

**Interfaces:**
- Produces: `SerialLink(port, baud=57600)` with `write(bytes)` and a non-blocking `read() -> bytes`, and `python -m droneload.comms --port PORT`, a bench tool: keys `d`, `g` and `a` send commands, and each reply and the state are printed.

- [ ] **Step 1: Write the failing test.** `test_serial_link_reads_what_is_waiting`, with `serial.Serial` replaced by a fake that has `in_waiting`.
- [ ] **Step 2: Run it and check it fails.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh`.**
- [ ] **Step 5: Update the docs and commit.** Message "Add the serial link to the robot".
- [ ] **Step 6: Bench test on a robot replica** (an Arduino running the protocol from annex 5): both alignments and a target, 5 runs in 5, with the drone's motors running nearby. Record the result in the README, marked as tested on the replica only.

### Task 4: Guiding and following the robot

**Files:**
- Create: `droneload/navigation/robot.py`
- Modify: `droneload/mission/runner.py` (`Context.robot`, polled each tick), `droneload/mission/plans.py`
- Test: `tests/test_navigation_robot.py`
- Docs: `droneload/navigation/README.md`, `docs/mission-map.md` (statuses), `docs/architecture.md` (state column), `TODO.md` ("`comms` protocol layer")

**Interfaces:**
- Consumes: `Robot`, `CentreOnMarker`'s `Centring`, `marker_offset_level`, `Context`.
- Produces: step `GuideRobot(timeout_s=180)`. Throughout, it centres the drone over marker 1 with `Centring`, which is the "follow the robot unaided" action. Its phases: send right and watch which way marker 1 moves in the level frame, to learn the rail's direction; drive toward marker 2 when it is in view, else sweep to the rail's end and back; send stop when marker 1's distance to marker 2 along the rail is under `STOP_LEAD_M` (the robot's speed times the measured stop delay; start at 0.05); read the reply; on `N`, pulse toward the marker for `NUDGE_S = 0.3` and stop again; repeat for marker 3; finish when `robot.target` is set, writing it to `ctx.notes["target"]`.

- [ ] **Step 1: Write the failing tests,** closed loop: a `FakeRobot` whose position moves marker 1 on a `sim_camera` floor each tick, markers 2 and 3 fixed beside the rail at the alignment points, a `KinematicVehicle` and the runner.

  - `test_guide_reads_the_target`: ends with `ctx.notes["target"] == 3`.
  - `test_drone_follows_the_robot`: the vehicle stays within 0.3 m of the robot while it moves and within 0.1 m once it has been stopped for 2 s.
  - `test_guide_works_from_either_heading`: the same with the drone facing the opposite way.
  - `test_guide_nudges_after_n`: with `align_tolerance_m=0.02`, at least one `N` is answered by a nudge and the run still ends with the target.
  - `test_guide_reverses_at_the_rail_end`, `test_guide_fails_on_silence`: as in Review Focus.
  - `test_guide_handles_both_reply_modes`.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh`.**
- [ ] **Step 5: Update the docs listed above and commit.** Message "Guide and follow the robot".

## Done When

- [ ] `GuideRobot` reads the target from the fake robot in every test configuration.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- Build the robot replica early: the real PULL-E is only met at the organisers' events.
- Measure the real robot's speed and stop delay at RCE3 and set `STOP_LEAD_M` from them.
- Ask the organisers whether the hidden markers 2 and 3 can be seen from above. The plan assumes they can.
