# stabilisation

Keeps the drone steady: level in the air, and holding its position indoors without GPS.

**Status:** [`indoor.parm`](indoor.parm) sets ArduPilot's estimator to use optical flow instead of GPS. It flies in the simulator, which also measures drift: about 5 cm over a 1 m move. Sensor drivers for the PMW3901 and a rangefinder are not set yet, and nothing here has been tested on a drone.

ArduPilot on the flight controller does the stabilising. Python on the companion computer must not run this loop, because it is too slow and must never get in the way of pilot takeover or the failsafe. Work here is mainly flight controller settings and tuning.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Stable-flight video | By RCE2, for +15 points | 2027 V0 |
| Qualification | Fly well for 2 minutes | 2027 V0 |
| Position hold | Within 0.5 m for 2 minutes, with no stick input | Proposed |

## Choosing the Fix

| What the drone does | Likely cause | Fix |
|---------------------|--------------|-----|
| Stays level but drifts sideways | No position hold | Set up Loiter mode, with optical flow and height sensing or beacons |
| Wobbles or oscillates | Poor tuning or vibration | Autotune or PID tuning; check the frame and propeller balance |
| Holds position but wanders over time | Sensor drift | Correct from ArUco markers, with velocity commands through `flight` |

## Vibration

Vibration affects both flight and the cameras, so it should be reduced at the source: balance the propellers, tighten the frame and motors, and soft-mount the flight controller and cameras. Check ArduPilot's vibration logs after test flights. Their use on this drone is unverified. Camera requirements are in the `vision` README.

## Open Questions

- Does optical flow need a rangefinder on this setup? It is not on the kit list. The simulator uses one, and ArduPilot gives no position on the ground until it has a height above ground. Not tried without one.
- Are Marvelmind beacons a better source of position than optical flow?
- What floor pattern will the organisers use? Details come at RCE2.

## Rules

- Commit settings files here, with a note on what changed and why.
- Test in simulation first, then with propellers removed where possible.
- Get a person's decision before writing code that talks to the flight controller.
