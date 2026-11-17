# Droneload 2027 Contest Summary

Summarised from the organisers' V1 rules (15 November 2026). Scoring is unchanged from V0. Annex 3 (target images), the robot code, the loan section and the repair rule are still marked as to be completed. Dates marked "portal" come from the team portal.

## Dates

| Date | Event | Source |
|------|-------|--------|
| 17 Oct 2026 | RCE0: remote presentation of the contest | V1 |
| 30 Oct 2026 | RCE1 at IPSA, Ivry-sur-Seine: each team presents its members and project. A Planète Sciences follower is assigned within a week | V1 |
| 30 Dec 2026 | Registration closes, with a progress sheet and a phone call | V1 |
| 15 Jan 2027 | RCE2 registration closes | Portal |
| 23 Jan 2027 | RCE2, Paris region: organisation, drone plans and programming logic, with an optional cage flight | V1 |
| 31 Jan 2027 | Planète Sciences membership closes | Portal |
| 24 Apr 2027 | RCE3, Paris region: cage flight, recognition and autonomous flight. The portal says 24-25 Apr | V1 |
| About 11 May 2027 | Written report due, one week before the final | V1 |
| 18-20 May 2027 | Final over 2 or 3 days, dates to be confirmed. Prizes are given at the end of the last day | V1 |
| 30 May 2027 | Image rights close | Portal |

Intermediate report versions are requested during the year, by email. News comes by email; technical exchanges happen on the Droneload Discord.

## Final

- **Written report:** 250 points, sent one week before.
- **Oral:** 250 points, 20 minutes plus 5-10 minutes of questions, before the flight test. Graded 45% technical work, 25% team organisation, 15% sharing of speaking time, including the questions, and 15% delivery.
- **Qualification, day 1:** the drone must fly well for 2 minutes, and the failsafe is tested.
- **Flight test:** days 1-2, or days 2-3 if the final runs 3 days, which would leave a day for cage tests.
- After qualification, changing the motor type, flight controller, its programming, remote or frame type needs approval.
- A team not ready for its slot can be disqualified.

## Points

Total 1,320: report 250, oral 250, flight test 670, bonus 150. Prizes: first, second and third, Junior, and a jury's favourite.

| Bonus | Points |
|-------|--------|
| Stable flight at RCE2, video accepted | 15 |
| 2-minute cage flight at RCE3, or a video of take-off with the object, drop on target and landing | 45 |
| Crash resistance, judged | 0-40 |
| Drone fully designed by the team, not using the loan kit or a commercial drone. Not counted for Junior | 50 |

## Drone Requirements

- 500 mm class maximum, 3 kg maximum at take-off for the drone alone, 5 minutes endurance, 200 m radio range.
- Pilot takeover at any time, failsafe for radio loss and low battery, and a remote kill-motor function.
- Any type or number of drones may be used.
- **For every scored action, the team must show the automatic detections on a screen the organisers provide**, as annotated video, text or similar.
- Powering up with propellers fitted needs approval from the on-site Planète Sciences operations director, or the team is disqualified.
- A safety note is issued before the final, and each team must sign it.

## Loan Kit

A loan agreement must be signed, and the equipment is returned after the contest. The partners lending equipment are Safran and Qualcomm; section 5 is still to be completed. Annex 1 lists the kit, lent on request and subject to stock:

| Item | Reference |
|------|-----------|
| Flight controller and GPS | Pixhawk 2.4.8 kit with GPS |
| Battery | LiPo 11.1 V 4200 mAh 3S |
| Motors | Brushless 2212 920 KV |
| ESC | 4 × 20 A |
| Propellers | 9450 |
| Frame and landing gear | F450 |
| Optical flow | MTF-01 |
| Remote and receiver | Flysky FS-i6X |
| Telemetry | 433 MHz kit |
| Positioning | One Marvelmind beacon. The 4 others needed are not lent, but are present at the final |
| Marvelmind cables | RP-SMA antenna extensions |
| Charger, tester, bag | Toolkit C6 charger, battery capacity tester, 23 × 18 cm LiPo bag |

Annex 1 lists no companion computer. The organisers have told the team a Qualcomm computer will be lent.

## Arena

Semi-indoor, possibly a covered tent, so GPS does not work. The cage is about 10 × 6 m and the playing field about 8 × 5 m, and both may change with the venue. A preparation room is provided, and a second cage for training if the venue allows.

The floor is either a black tarp with a pattern for optical flow, or the bare ground, such as concrete with gravel, with markings taped on. The organisers will say which. The rules warn that the black tarp may stop ToF and infrared distance sensors working outdoors.

Beacons are unlimited, but must sit outside the playing field.

| Area | Content and marking |
|------|---------------------|
| Playing field | Red and white floor lines, red on the inside |
| A | Take-off and landing area, with ArUco 0. Blue marking |
| B | Central zone, also called the complex environment: the only zone with obstacles and objects over 50 cm tall. Blue and white lines, white on the inside, absent along the field edge |
| C | Drop and robot zone, also called the hovering zone, with four A3 target posters. Blue marking |
| D | Safe path: green line on the right and yellow on the left, seen from the pilot station, with no obstacle within 50 cm either side |
| E | One 100 × 100 cm window, at a random height |
| F | Obstacles. Annex 6 shows one, but colours and pictures will differ |
| G | Robot, on a rail, with ArUcos 2 and 3 behind a visual barrier |

**Layout, from Figure 1.** The pilot station stands outside one short side of the field, facing C at the far end. A is the near corner on the pilot's right. B fills the middle, with the window E near its centre and two obstacles F. The safe path D runs in an S-curve from A to the edge of C. Inside C, the robot's rail runs across the field next to B, the hidden ArUcos 2 and 3 sit behind it, and the posters 1, 3, 2 and 4 line the far edge, in that order from the pilot's right to left. No dimensions are given.

## Flight Test

One 15-minute run, from motor start to propeller stop, with 10 minutes of setup before it. Battery swaps do not stop the clock. V1 allows one 30-minute repair, and marks this as still to be updated. The two missions run in the same 15 minutes, in any order.

During automatic flight, the operator may only confirm that an action has finished. Any other command, such as selecting the target, scores in the manual column.

**Part 1, drop and cooperation:** take off from A with an object fitted by hand under the drone. The referee picks a target at random, and the drone drops the object on it. The drone then steers the robot in front of each hidden ArUco to get a second target, and drops an object there. There are 2 to 4 decoy images, revealed at the final. After a miss, the team can fetch another object from zone A.

**Objects:** circular, 50 g at most, with a Ø40 mm ferrous plate for a magnet and a Ø62 mm ring for a mechanical grip. The grabber is the team's choice. Teams may bring their own objects of similar size and mass, checked at qualification.

**Part 2, complex environment:** take off from A, cross by the window or the safe path, hover for 5 s in zone C or do a zone C action, return the same ways, and land in A. Retries are allowed within the 15 minutes.

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

20 × 20 cm, from a 4x4 dictionary. V1 lists the dictionary as "4x4 (50, 100, 250, 100)", generated with fodi.github.io/arucosheetgen or chev.me/arucogen. The robot photos in annex 5 decode as ID 1 in `DICT_4X4_50`.

| Element | ID |
|---------|----|
| Zone A | 0 |
| Robot | 1 |
| Robot alignment targets | 2, 3 |
| Window, side facing the pilot (A to C) | 4 right/bottom, 5 right/top, 6 left/top, 7 left/bottom |
| Window, far side (C to A) | 8 bottom, 9 top |

The four corner markers sit at the window's corners but not on its diagonals. The two far-side markers are above and below the opening, vertically aligned but off-centre. Exact positions are not given, and the drawings use placeholder markers.

## Robot

The robot, PULL-E, moves left and right on a rail and starts stopped. It can also be driven by hand, probably through a web page over a Wi-Fi hotspot or an IR remote.

UART at 57600 baud, 8N1, no flow control. Send `D` (0x44) right, `G` (0x47) left, `A` (0x41) stop. The robot stops at either end of its rail. A team module can sit on top of the robot, in front of its ArUco, connected by 5 V, GND, RX and TX female Dupont cables. The 5 V supply can power an Arduino, but not a Raspberry Pi. A Raspberry Pi's 3.3 V UART must not be connected directly to an Arduino's 5 V UART.

After a stop, the robot replies 3 times with `N` (0x4E, not aligned), `F` (first alignment OK) or `S` (0x53, second alignment OK). When both are complete, it picks a target at random and sends a digit naming the target image.

LEDs show the same for the public: blue blinks for an alignment, red blinks for a failed one, and for the target X, X blue then X red blinks, repeated.

## Organisers' Software Advice

From the first-call slides: use OpenCV with Python for vision, simulate flight with Gazebo and ArduPilot, and use MAVLink with QGroundControl or Mission Planner. Test each component alone before integration.

## Open Questions

- What are the target images? Annex 3 is not published. The theme is "Saveurs savantes", and the introduction hints at food (🍩, 🍣).
- Where is the final? V1 says only "at a leading aerospace company's premises".
- Will the arena be a tent, and will the floor be the black tarp or bare ground?
- What is the final repair rule? Section 8 points to "part 4" for it, which does not exist.
- Which byte means `F`? V1 prints 0x56, but ASCII `F` is 0x46.
- Does the robot reply 3 times after a stop, as in annex 5, or every 100 ms, as in section 7.4.1? Annex 5's LED table also shows other UART messages ("Première couleur Okay").
- Section 7.4.1 says the robot's speed can be changed, but the UART protocol has no speed command. How?
- How does the drone receive the referee's target without a manual command?
- Several places still say "cube", but the objects are circular. Are any cubes used?
- The slides give 135 for the Part 2 Junior total, but the V1 colours give 140. Which is right?
- The slides give a manual total of 40, but the V1 tables give 50. Which is right?
- What are the safe path line width, the window marker positions and the field dimensions in Figure 1?
- Which Qualcomm computer is lent, and is it covered by the loan agreement in section 5?
