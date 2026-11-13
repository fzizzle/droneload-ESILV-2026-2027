# tracking

Keeps detections steady and reliable from frame to frame, despite camera vibration. This covers software only. Flight stability is in `droneload/flight/stabilisation`, and camera shutter, exposure and mounting are in the `vision` README.

**Status:** Confirming across frames and smoothing positions are done, in `tracker.py`, and on by default in the detection loop (`--no-track` turns them off). Nothing here has been tested on a real camera or in flight.

## Planned Work

Listed in the order to try them. Start with the simplest that works.

| Method | What it does | Limit |
|--------|--------------|-------|
| Confirm across frames | Accept a marker only if it is seen in several recent frames | Adds a short delay |
| Smooth positions | Filter marker positions over time, to steady centring and landing | Lags behind real movement |
| Skip poor frames | Discard frames that are too blurred, using a sharpness measure | Fewer frames to work with |
| Use drone motion | Correct positions using the flight controller's attitude data | Needs matching timestamps, and goes through `flight` |
| Stabilise whole images, as a last resort | Align frames with OpenCV optical flow. Try it only if real footage shows a need; it may help the jury display, line following or search | Costs processing time and adds delay. ArUco detection works on single frames, so it will not fix blur on its own |

## Results

Settings are at the top of `tracker.py`: a marker is reported after 3 hits in the last 5 frames, a jump over 40 px starts a new track, and the new position has a weight of 0.6.

On Shadow-ArUco `video_5` (`python -m testing.benchmark --track`):

| Setting | Found | Unmatched |
|---------|-------|-----------|
| No tracking | 56.4% | 26.6% |
| 2 of 5 frames | 55.0% | 6.1% |
| 3 of 5 frames (chosen) | 53.2% | 2.4% |

Smoothing did not change these scores, because the benchmark accepts positions within 15 px. Confirming adds about 2 frames of delay, 67 ms at 30 frames per second. That footage uses another dictionary and was not filmed from a drone.

Software cannot recover a marker that is badly blurred or distorted. It works alongside a global-shutter camera, short exposure and soft mounting, and does not replace them.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Detection display | Must still show detections live to the jury | 2027 V0 |
| Added delay | No more than a few frames, so control stays responsive | Proposed |
| Processing time | Measured on the companion computer, within the 30 frames per second target | Proposed |

## Measuring

- Use `python -m testing.benchmark` before and after each change, and `python -m testing.vibration_test` for vibration.
- Judge it on real flight footage when available.
