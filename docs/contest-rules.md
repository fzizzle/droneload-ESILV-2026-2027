# Droneload 2027 Contest Summary

Summarised from the organisers' V0 rules (October 2026). V0 is a first version: annexes 1 and 3, the robot code, the loan section and the repair rule are marked as still to be completed, and some 2026 text remains. Dates marked "portal" come from the team portal, because V0 leaves them blank.

## Dates

| Date | Event | Source |
|------|-------|--------|
| 30 or 31 Oct 2026 | RCE1: each team presents its members and project. A Planète Sciences follower is assigned within a week | V0 says 30 Oct, portal says 31 Oct |
| 31 Dec 2026 | Registration closes | V0 |
| 15 Jan 2027 | RCE2 registration closes | Portal |
| 23 Jan 2027 | RCE2: organisation, drone plans and programming logic, with an optional cage flight | Portal date, V0 content |
| 31 Jan 2027 | Planète Sciences membership closes | Portal |
| 24-25 Apr 2027 | RCE3: cage flight, recognition and autonomous flight | Portal date, V0 content |
| 30 May 2027 | Image rights close | Portal |
| May or July 2027 | Final over two days. V0 gives both months | V0 |
| One week before the final | Written report due | V0 |

Intermediate report versions are requested during the year, by email.

## Final

- **Day 1:** oral (20 minutes, plus 5-10 minutes of questions), then drone inspection and test flights.
- **Day 2:** flight test.
- The drone must fly well for 2 minutes at qualification, and the failsafe is tested there.
- After qualification, changing the motor type, flight controller, its programming, remote or frame type needs approval.
- A team not ready for its slot can be disqualified.

## Points

Total 1,320: report 250, oral 250, flight test 670, bonus 150.

| Bonus | Points |
|-------|--------|
| Stable flight at RCE2, video accepted | 15 |
| 2-minute cage flight at RCE3, or a video of take-off with the object, drop on target and landing | 45 |
| Crash resistance, judged | 0-40 |
| Drone fully designed by the team, not using the loan kit or a commercial drone. Not counted for Junior | 50 |

## Drone Requirements

- 500 mm class maximum, 3 kg maximum at take-off, 5 minutes endurance, 200 m radio range.
- Pilot takeover at any time, failsafe for radio loss and low battery, and a remote kill-motor function.
- Any type or number of drones may be used.
- Powering up needs approval from the on-site Planète Sciences operations director, or the team is disqualified.
- A safety note is issued before the final, and each team must sign it.
- Loan kit list from the first-call slides, because annex 1 is not published: DJI F450 frame, Pixhawk 2, GPS, Flysky FS-i6, Marvelmind beacons, PMW3901 optical flow, 433 MHz telemetry, and a companion computer on request. Loaned equipment is returned after the contest.

## Arena

Indoors, so GPS does not work. The cage is about 10 × 6 m and the playing field about 8 × 5 m, and both may change with the venue. A floor pattern helps optical flow, with details at RCE2. Beacons are unlimited, but must sit outside the playing field.

| Zone | Content |
|------|---------|
| A | Take-off and landing area, with ArUco 0 |
| B | Central zone: the only zone with obstacles and objects over 50 cm tall |
| C | Drop and robot zone, also called the hovering zone, with four A3 target posters |
| D | Safe path: green line on the right and yellow on the left, seen from the pilot station, with no obstacle within 50 cm either side |
| E | One 100 × 100 cm window, at a random height |
| F | Obstacles |
| G | Robot zone, with ArUcos behind a visual barrier |

## Flight Test

One 15-minute run, from motor start to propeller stop, with 10 minutes of setup before it. Battery swaps do not stop the clock. V0 allows one 30-minute repair, and marks this as still to be updated.

During automatic flight, the operator may only confirm that an action has finished. Any other command, such as selecting the target, scores in the manual column.

**Part 1, drop and cooperation:** the referee picks a target at random, and the drone drops an object on it. The drone then steers the robot in front of each hidden ArUco to get a second target, and drops an object there. There are 2 to 4 decoy images, revealed at the final. After a miss, the team can fetch another object from zone A.

**Part 2, complex environment:** take off from A, cross by the window or the safe path, hover for 5 s in zone C or do a zone C action, return the same ways, and land in A. Retries are allowed.

Junior column: **yes** counts in full. **Manual** counts only the manual value. **No** does not count.

| Action | Times | Manual | Automatic | Junior |
|--------|-------|-------:|----------:|--------|
| Drop, first ground contact on target | 2 | 10 | 20 | Yes |
| Recognise a delivery zone | 2 | -5 | 10 | Yes |
| Search for the delivery zone | 2 | | 30 | No |
| Follow the robot unaided | 1 | 10 | 30 | Manual |
| Robot steps and second drop automatic | 1 | | 40 | No |
| Follow the safe path | 2 | | 30 | Yes |
| Window, A to C | 1 | 10 | 30 | Yes |
| Window, C to A | 1 | 10 | 50 | Manual |
| Window carrying an object | 2 | 5 | 10 | Manual |
| Automatic round trip on the safe path, with take-off and landing on ArUco 0 | 1 | | 30 | Yes |
| Automatic round trip off the safe path, same conditions | 1 | | 70 | No |
| Automatic take-off | 1 | | 10 | Yes |
| Automatic landing, anywhere | 1 | | 10 | Yes |
| Full automatic mission, take-off to landing in A | 2 | | 100 | No |

A full mission combines one drop task (referee target, or robot and its target) with one crossing (safe path, or off the safe path). No element may be used in both missions, so the second 100 points needs the robot and the crossing off the safe path.

Maximum: 190 for Part 1, 260 for Part 2 and 220 common, making 670.

## ArUco Markers

20 × 20 cm, from a 4x4 dictionary. V0 lists the dictionary as "4x4 (50, 100, 250, 100)".

| Element | ID |
|---------|----|
| Zone A | 0 |
| Robot | 1 |
| Robot alignment targets | 2, 3 |
| Window, side facing the pilot | 4 right/bottom, 5 right/top, 6 left/top, 7 left/bottom |
| Window, far side | 8 bottom, 9 top |

The four corner markers are not on the window's diagonals. The two far-side markers are vertically aligned, but off-centre. Exact positions are not given.

## Robot

UART at 57600 baud, 8N1, no flow control. Send `D` (0x44) right, `G` (0x47) left, `A` (0x41) stop. V0 shows a team module on top of the robot, in front of its ArUco, connected by 5 V, GND, RX and TX Dupont cables. The 5 V supply can power an Arduino, but not a Raspberry Pi. A Raspberry Pi's 3.3 V UART must not be connected directly to an Arduino's 5 V UART.

After a stop, the robot replies 3 times with `N` (0x4E, not aligned), `F` (first alignment OK) or `S` (0x53, second alignment OK). When both are complete, it sends a digit naming the target image.

## Organisers' Software Advice

From the first-call slides: use OpenCV with Python for vision, simulate flight with Gazebo and ArduPilot, and use MAVLink with QGroundControl or Mission Planner. Test each component alone before integration.

## Open Questions

- Is RCE1 on 30 or 31 October?
- Is the final in May or July, and where? RCE2 and RCE3 dates are blank in V0.
- What are the target images? Annex 3 is not published. The theme is "Saveurs savantes".
- Part 2 still says "during the 10 minutes", and elsewhere the run is 15 minutes. Which is right?
- What is the final repair rule?
- Which byte means `F`? V0 prints 0x56, but ASCII `F` is 0x46.
- Does the robot reply 3 times after a stop, as in annex 5, or every 100 ms, as in section 7.4.1?
- How does the drone receive the referee's target without a manual command?
- The slides give 135 for the Part 2 Junior total, but the V0 colours give 140. Which is right?
- The slides give a manual total of 40, but the V0 tables give 50. Which is right?
- What are the safe path line width and the exact window marker positions?
