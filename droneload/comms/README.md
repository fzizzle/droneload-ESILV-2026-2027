# comms

Talks to the ground robot PULL-E: sends movement commands and reads its replies.

**Status:** Not started. The 2027 protocol is not confirmed, so everything below comes from the 2026 rules unless marked.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Control | UART (5 V pin available) or remote | 2027 slides |
| Robot reply | Sends a code naming the drop target over UART | 2027 slides |
| Automatic robot step | 40 points | 2027 slides |
| UART settings | 57600 baud, 8N1 | 2026 rules |
| Commands to robot | `D` (0x44) right, `G` (0x47) left, `A` (0x41) stop | 2026 rules |
| Replies from robot, sent 3 times after a stop | `N` (0x4E) not aligned, `F` first alignment OK, `S` (0x53) second alignment OK | 2026 rules |
| Reliability | Both alignments and a target ID in 5 bench runs out of 5 | Proposed |

The previous team reached a robot replica through two HC-12 radio modules, at the same settings. Whether a radio link is allowed in 2027 is not confirmed.

## Wiring Warnings

- A Raspberry Pi's UART runs at 3.3 V and an Arduino's at 5 V. Connecting them directly destroys the Pi's port, so use a level converter.
- The robot's 5 V pin can power an Arduino, but not a Raspberry Pi.

## Open Questions

- Is the 2027 protocol the same as 2026?
- Which byte means `F`? The 2026 rules print 0x56, but ASCII `F` is 0x46. Accept both until confirmed.

## Uses

Nothing from other modules. Only this module talks to the robot.
