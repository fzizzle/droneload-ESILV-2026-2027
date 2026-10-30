# Droneload 2027 Contest Summary

**English** | [Français](contest-rules.fr.md)

**Provisional.** This comes from the organisers' first-call slides and the team portal (27 Oct 2026), because no written 2027 rules exist yet. Where the slides say nothing, the 2026 rules are the best guide. Re-check every number when the 2027 PDF appears.

## Deadlines

| Date | Event |
|------|-------|
| 31 Oct 2026 | RCE1 (what is due is not stated) |
| 15 Jan 2027 | RCE2 registration closes |
| 23 Jan 2027 | RCE2: stable-flight video earns +15 |
| 31 Jan 2027 | Planète Sciences membership closes |
| 24-25 Apr 2027 | RCE3: 2-minute cage flight or drop video earns +45 |
| 30 May 2027 | Image rights close |
| Not given | Report drafts, final report, oral, final |

## Points

Total 1,320: report 250, oral 250, flight test 670, bonus 150.

## Drone Requirements

- 500 mm class maximum, 3 kg maximum, 5 minutes endurance, 200 m radio range.
- Pilot override at any time, failsafe on radio loss or low battery, and a kill-motor function.
- Loan kit: DJI F450 frame, Pixhawk 2, GPS, Flysky FS-i6, Marvelmind beacons, PMW3901 optical flow, 433 MHz telemetry, and a companion computer on request.
- 2026 rule: powering up needs approval from the on-site Planète Sciences operations director, or the team is disqualified.

## Arena

Mat of about 8 × 5 m in a 10 × 6 m netted cage. Printed markers lie on the mat floor. The slides describe indoor flight without GNSS, so plan for beacons, optical flow or vision. The 2026 drop and cooperation test ran in an outdoor cage, so lighting may vary.

| Zone | Content |
|------|---------|
| A | Take-off and landing pad, with ArUco |
| B | Complex environment: objects over 50 cm tall |
| C | Drop and robot zone, targets 1-4 |
| D | Safe path: a line, with no obstacle within 50 cm either side |
| E | One 100 × 100 cm window: 4 corner ArUcos going out (easy), 2 coming back (hard) |
| F | Akilux totems, floor to cage roof |
| G | Visual barrier hiding ArUcos; the robot drives along it |

Robot PULL-E carries a large ArUco on top and sends a code naming the drop target over UART. It can be driven by UART or remote.

## Flight Test

One 15-minute run, from motor start to propeller stop. Maximum automatic points are shown. A manual-only run scores 40 at most.

| Part | Tasks | Max |
|------|-------|-----|
| 1: Drop and cooperation | Drop on called targets, search for and recognise delivery zones, hold on the robot, align the robot with the hidden ArUco | 190 |
| 2: Complex environment | Safe path, window both ways, carry an object through, automatic round trip | 260 |
| Common | Automatic take-off and landing; two full automatic missions at 100 each | 220 |

## Organisers' Software Advice

Use OpenCV with Python for vision, simulate flight with Gazebo and ArduPilot, and use MAVLink with QGroundControl or Mission Planner. Test each component alone before integration.

## ArUco Markers

The 2027 IDs are not published. `ARUCO_LABELS` in `droneload/vision/detect.py` matches annex 4 of the 2026 rules, and 2026 markers were 20 × 20 cm from a 4x4 dictionary. 2026 had two windows and 12 window markers; 2027 has one window with 6 markers, so IDs 4-15 may change.

## Open Questions

- Date and venue of the final, and what is due at RCE1.
- Report deadlines and the RCE3 registration close.
- Slides say "135 points max" per part, but the tables give 190 and 260.
- The manual total is given as 40, but the stated part maxima (20 and 30) add up to 50.
- Whether the robot's UART protocol matches 2026.
