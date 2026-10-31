# tracking

Keeps detections steady and reliable from frame to frame, despite camera vibration. This covers software only. Flight stability is in `droneload/flight/stabilisation`, and camera shutter, exposure and mounting are in the `vision` README.

**Status:** Not started. Nothing here has been tested on a real camera or in flight.

## Planned Work

Listed in the order to try them. Start with the simplest that works.

| Method | What it does | Limit |
|--------|--------------|-------|
| Confirm across frames | Accept a marker only if it is seen in several recent frames | Adds a short delay |
| Smooth positions | Filter marker positions over time, to steady centring and landing | Lags behind real movement |
| Skip poor frames | Discard frames that are too blurred, using a sharpness measure | Fewer frames to work with |
| Use drone motion | Correct positions using the flight controller's attitude data | Needs matching timestamps, and goes through `flight` |

Confirming across frames may also reduce false detections, such as the wrong IDs seen on Shadow-ArUco. This is untested.

Whole-image stabilisation is left out: ArUco detection works on single frames, so aligning frames would not undo blur or distortion.

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
