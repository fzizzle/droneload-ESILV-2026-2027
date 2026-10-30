# flight

Sets up the flight controller so the drone holds position indoors, and gives the rest of the code one safe way to command it.

**Status:** Not started. Nothing here commands a drone yet. Get a person's decision before writing code that does.

**Assumed, not decided:** ArduPilot on the Pixhawk, reached over MAVLink. The previous team flew this setup, and the organisers suggest it.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Size and mass | 500 mm class at most, 3 kg at most, with computer and cameras included | 2027 slides |
| Endurance | At least 5 minutes | 2027 slides |
| Radio range | At least 200 m | 2027 slides |
| Pilot takeover | Possible at any moment | 2027 slides |
| Failsafe | Automatic landing or stop on radio loss or low battery | 2027 slides |
| Kill-motor function | Required | 2027 slides |
| Positioning | No GNSS indoors: use optical flow, rangefinder, beacons or vision | 2027 slides |
| Beacons | Allowed in the flight area, not on the mat | 2027 slides |
| Powering up | Needs approval from the on-site operations director, or the team is disqualified | 2026 rules |
| Stable-flight video | By RCE2, 23 January 2027, for +15 points | 2027 slides |
| Two-minute cage flight, or a drop video | At RCE3, 24-25 April 2027, for +45 points | 2027 slides |
| Automatic take-off and landing | 10 points each | 2027 slides |
| Position hold | Within 0.5 m for 2 minutes, with no stick input | Proposed |
| Connection loss | Send zero velocity when the mission stops sending commands | Proposed |
| Pilot takeover in code | Any mode change away from Guided ends the mission | Proposed |

## Done When

- A simulator script takes off to 1 m, moves 1 m forward and lands.
- Changing mode in mid-flight stops the script.
- Failsafes are tested with propellers removed.
- Flight controller settings are committed here.

## Risks

- Optical flow can drift over the venue floor, so positions wander.
- Test everything in simulation first. Nothing goes on the drone until it has passed there.

## Uses

Nothing from other modules. Only this module talks to the flight controller.
