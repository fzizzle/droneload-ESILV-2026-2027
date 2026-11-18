# Loan Kit Bring-Up Plan

> **For the people doing this:** this is a hardware checklist, not code. Work through the stages in order and do not skip a pass check. Steps use checkbox (`- [ ]`) syntax for tracking. Record each result in the branch log, in two lines at most.

**Goal:** Take the loan kit from the box to a 2-minute hands-off hover in Loiter on the MTF-01, with every failsafe tested, and film it for the RCE2 bonus (+15, by 23 January 2027).

**Approach:** Bench work with propellers off first, then manual flight, then position hold. Every setting that works is committed as a `.parm` file in `droneload/flight/stabilisation/`, so the drone can be rebuilt from the repository.

**Sources:** `docs/contest-rules.md` (annex 1 kit, qualification, safety), ArduPilot's MTF-01 and optical flow setup pages (read 2026-11-18). Parameter values below come from those pages and are **unverified on this hardware**.

## Global Constraints

- **Propellers stay off until Stage 4.** At any organisers' event, powering up with propellers needs the operations director's approval.
- ArduPilot Copter 4.7.2, the version `scripts/sim.sh` pins, so the simulator and the drone match.
- One change at a time, then a test. Save the full parameter list before and after each stage.
- `droneload.flight` refuses to connect to a real drone. Stage 6 needs the project lead's decision before any code changes that.
- Nothing counts as tested unless it ran on the kit. Mark everything else unverified.
- Branch `chore/kit-bring-up`, log `logs/YYYY-MM-DD-chore-kit-bring-up.md`.

## Risks to Settle Early

1. **Black tarp.** The rules warn it may stop ToF sensors. The MTF-01's rangefinder is ToF, and optical flow cannot work without a height. Stage 3 measures this.
2. **Flash size.** Some Pixhawk 2.4.8 boards can use only 1 MB of flash, and that firmware build leaves features out. Stage 1 checks optical flow and precision landing are present.
3. **Serial ports.** The telemetry radio, the MTF-01 and the companion computer each need one.
4. **Compass indoors.** Steel in a building bends the heading. Stage 5 measures it.
5. **Position on the ground.** Automatic take-off needs the estimator to give a position before the drone leaves the floor.

---

### Stage 0: Unpack and record

- [ ] Check every item against annex 1 in `docs/contest-rules.md`. Photograph the kit. Note anything missing or damaged and tell the organisers the same day.
- [ ] **Identify the Qualcomm computer:** exact model, camera connectors, USB ports, UART voltage, and what powers it. This unblocks the camera purchase (`TODO.md`, Hardware to get).
- [ ] Check the battery: each cell between 3.7 and 4.2 V and within 0.05 V of the others. Charge it in the LiPo bag.
- [ ] Find the ToF sensor and the two electromagnets from the old inventory and note whether they are still in the box.
- [ ] Weigh the assembled drone. The limit is 3 kg, computer, cameras and grabber included.

**Pass:** an inventory in the log, and the computer's model in `logs/DECISIONS.md`.

### Stage 1: Firmware and basic setup (propellers off)

- [ ] Flash Copter 4.7.2 with Mission Planner or QGroundControl. Note which board build it chose (`Pixhawk1` or `Pixhawk1-1M`).
- [ ] Refresh the parameters and search for `FLOW_TYPE` and `PLND_ENABLED`. If either is missing, the build left the feature out: note it, and see ArduPilot's custom firmware build server before going on.
- [ ] Set the frame to Quad X. Run the accelerometer, compass and radio calibrations, then the ESC calibration.
- [ ] Run the motor test and check each motor's position and direction against ArduPilot's Quad X diagram.
- [ ] Calibrate the battery monitor against a multimeter.
- [ ] Put Stabilize, AltHold and Loiter on the FS-i6X mode switch. Any switch move must leave Guided, because that is how the pilot takes over (`PilotTakeover` in `vehicle.py`).
- [ ] Set a second switch to motor emergency stop (`RCx_OPTION = 31`). The rules require a remote kill.

**Pass:** all four motors spin the right way, the modes change from the transmitter, and the kill switch stops the motors on the bench.

### Stage 2: Failsafes (propellers off)

- [ ] Radio loss: set `FS_THR_ENABLE` to land. Arm, switch the transmitter off, and check the mode goes to Land.
- [ ] Low battery: set `BATT_LOW_VOLT` and `BATT_FS_LOW_ACT` to land. Start at 10.5 V for the 3S pack and adjust after the first flights.
- [ ] Load `droneload/flight/failsafe.parm` and read back `FS_GCS_ENABLE = 5` and `FS_GCS_TIMEOUT = 3`.
- [ ] Commit the working values as `droneload/flight/stabilisation/kit.parm`, with a comment per line.

**Pass:** each failsafe shows its mode change on the ground station. This is what qualification tests on day 1.

### Stage 3: MTF-01 optical flow and rangefinder (propellers off)

- [ ] With MicoAssistant and a USB-serial adapter, set the sensor's protocol to `mav_apm` and its `mav_id` to 200.
- [ ] Choose the ports. Proposed: TELEM1 for the 433 MHz radio, TELEM2 for the companion computer, SERIAL4 for the MTF-01. Confirm against the board's connectors.
- [ ] Set, for the MTF-01's port `x`: `SERIALx_BAUD = 115`, `SERIALx_PROTOCOL = 1`, reboot, then `MAVn_OPTIONS = 2` for that MAVLink channel, `FLOW_TYPE = 5`, `RNGFND1_TYPE = 10`, reboot, then `RNGFND1_MAX = 8`, `RNGFND1_MIN = 0.01`, `RNGFND1_ORIENT = 25`.
- [ ] Check the ground station shows a non-zero `opt_qua` and a `rangefinder1` reading that follows the drone when lifted by hand.
- [ ] **Flow direction check.** Set `LOG_DISARMED = 1`. Hold the drone level at eye height over a textured floor and rock it ±15° in roll, then pitch, five times each. In the log, `OF.bodyX` must follow `IMU.GyrX` with the same sign, and likewise Y. If the sign is opposite, set `FLOW_ORIENT_YAW = 18000` and repeat. A wrong sign causes a flyaway.
- [ ] Scale `FLOW_FXSCALER` and `FLOW_FYSCALER` until `OF.flowX` and `OF.bodyX` match in size.
- [ ] **Black tarp test.** Over a matt black tarp or cloth, then over a patterned floor, record the rangefinder reading and `opt_qua` at 0.5, 1.0, 1.5 and 2.0 m, indoors and in daylight. Put the table in the stabilisation README.
- [ ] Commit the values as `droneload/flight/stabilisation/mtf01.parm`, and update the README's open question on the rangefinder.

**Pass:** flow and gyro agree in sign and size, and the range reads within 10 cm from 0.5 to 2 m over the patterned floor. If the black tarp fails, tell the organisers and price a second rangefinder; do not buy before the project lead decides.

### Stage 4: First flights, manual (propellers on)

Needs a net, a cage or an empty hall, a spotter, and the kill switch tested that day.

- [ ] Leave the estimator off the flow: `EK3_SRC1_VELXY = 0`. Hover in Stabilize, then AltHold, between 0.5 and 3 m, with small stick movements.
- [ ] In the log, check `VIBE` stays under 30 m/s² with no clipping. If not, balance the propellers and soft-mount the flight controller before going on.
- [ ] Check `EKF5.meaRng` follows the height and the flow values vary with movement.
- [ ] Note the hover throttle and the flight time to the low-battery failsafe. The rules ask for 5 minutes.

**Pass:** a steady AltHold hover and a clean vibration log.

### Stage 5: Position hold on optical flow (propellers on)

ArduPilot asks for about 15 m of clear space for this first test.

- [ ] Load `droneload/flight/stabilisation/indoor.parm` (`EK3_SRC1_VELXY = 5`, `EK3_SRC1_POSXY = 0`) and set the estimator's origin from the ground station.
- [ ] Take off in Loiter to 1 m. If it speeds away, switch to AltHold and land.
- [ ] Hold for 2 minutes with hands off the sticks. Measure the drift against tape on the floor. Target: within 0.5 m.
- [ ] Yaw check: rotate the drone 360° by hand on the ground, at three places in the room, and compare the reported heading with a floor line. Note the worst error.
- [ ] Before take-off, note whether Loiter arms on the ground with no GPS, and the pre-arm message if it refuses.
- [ ] **Film a 2-minute hover for the RCE2 bonus** and send it as the organisers ask.

**Pass:** 2 minutes within 0.5 m. This is the "Position hold" requirement in the `flight` README and the qualification test.

### Stage 6: Companion computer link (propellers off)

Blocked until the project lead decides when `flight` may connect to a real drone (`TODO.md`).

- [ ] Wire the companion computer's UART to TELEM2 through a level converter if its UART is not 3.3 V. Set `SERIAL2_PROTOCOL = 2` and agree the baud rate.
- [ ] Bench test, propellers off: connect, arm in Guided, then kill the program. The mode must change to Land within 3 s.
- [ ] Bench test: move the mode switch during a run. The program must stop with `PilotTakeover`.
- [ ] Tick "Failsafes are tested with propellers removed" in the `flight` README.

**Pass:** both bench tests behave as they do in the simulator.

### Stage 7: Flight footage

- [ ] Fix a phone or the chosen camera under the drone, pointing down. Lay printed `DICT_4X4_50` markers 0 to 9, 20 cm wide, on the floor.
- [ ] Record a hover at 1, 1.5 and 2 m, and a slow pass over the markers. Keep the files in `test_footage/flight/`, which is not committed.
- [ ] Run `python -m droneload.vision --source FILE --record out.mp4` and note the share of frames in which each marker is confirmed.

**Pass:** real numbers replace the simulated shake figures in the `vision` README. This closes "Measure vibration in flight" in `TODO.md`.

## Done When

- [ ] `kit.parm` and `mtf01.parm` are committed and rebuild the setup from a fresh flash.
- [ ] The stabilisation README holds the black tarp table, the drift figure and the heading error.
- [ ] The RCE2 video is sent.
- [ ] `docs/mission-map.md` marks "Load the indoor position settings" and "Hold position without GPS" as built.
