# comms

Talks to the ground robot PULL-E: sends movement commands and reads its replies.

**Status:** Not started. V0 repeats the 2026 protocol, but the robot code is still marked as to be updated.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Control | UART (5 V pin available) or remote | 2027 V0 |
| Robot reply | Sends a code naming the drop target over UART | 2027 V0 |
| Automatic robot step | 40 points | 2027 V0 |
| UART settings | 57600 baud, 8N1, no flow control | 2027 V0 |
| Commands to robot | `D` (0x44) right, `G` (0x47) left, `A` (0x41) stop | 2027 V0 |
| Replies from robot, sent 3 times after a stop | `N` (0x4E) not aligned, `F` first alignment OK, `S` (0x53) second alignment OK | 2027 V0 |
| Target code | A digit naming the target image, after both alignments | 2027 V0 |
| Team module on the robot | Sits in front of its ArUco, on 5 V, GND, RX and TX Dupont cables | 2027 V0 |
| Reliability | Both alignments and a target ID in 5 bench runs out of 5 | Proposed |

The previous team reached a robot replica through two HC-12 radio modules, at the same settings. V0's team module fits that approach, but it does not state which links are allowed.

## Wiring Warnings

- A Raspberry Pi's UART runs at 3.3 V and an Arduino's at 5 V. Connecting them directly destroys the Pi's port, so use a level converter.
- The robot's 5 V pin can power an Arduino, but not a Raspberry Pi.

## Open Questions

- Which byte means `F`? V0 prints 0x56, but ASCII `F` is 0x46. Accept both until confirmed.
- Does the robot reply 3 times after a stop (annex 5) or every 100 ms (section 7.4.1)? Handle both until confirmed.

## Uses

Nothing from other modules. Only this module talks to the robot.
