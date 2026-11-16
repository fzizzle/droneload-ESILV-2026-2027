# tracking

Keeps detections steady and reliable from frame to frame, despite camera vibration. This covers software only. Flight stability is in `droneload/flight/stabilisation`, and camera shutter, exposure and mounting are in the `vision` README.

**Status:** Confirming across frames is done, in `tracker.py`, and on by default in the detection loop (`--no-track` turns it off). Smoothing was tried and is off (`SMOOTHING = 1.0`), because it made logged positions lag. Nothing here has been tested on a real camera or in flight.

## Planned Work

Listed in the order to try them. Start with the simplest that works.

| Method | What it does | Limit |
|--------|--------------|-------|
| Confirm across frames | Accept a marker only if it is seen in several recent frames | Adds a short delay |
| Smooth positions (tried, off) | Filter marker positions over time, to steady centring and landing | Lags behind real movement. For steering, filter in `navigation` instead (see below) |
| Skip poor frames | Discard frames that are too blurred, using a sharpness measure | Fewer frames to work with |
| Use drone motion | Correct positions using the flight controller's attitude data | Needs matching timestamps, and goes through `flight` |
| Stabilise whole images, as a last resort | Align frames with OpenCV optical flow. Try it only if real footage shows a need; it may help the jury display, line following or search | Costs processing time and adds delay. ArUco detection works on single frames, so it will not fix blur on its own |

## Results

Settings are at the top of `tracker.py`: a marker is reported after 3 hits in the last 5 frames, a marker may move up to 0.75 of its side length per frame since it was last seen (at least 20 px), and the reported position is the detected one (`SMOOTHING = 1.0`). A far detection never moves a confirmed marker: it counts as a miss, so a single false positive with the same ID cannot replace it.

On Shadow-ArUco `video_5` (`python -m testing.benchmark --track`):

| Setting | Found | Unmatched |
|---------|-------|-----------|
| No tracking | 56.4% | 26.6% |
| 2 of 5 frames | 55.1% | 7.1% |
| 3 of 5 frames, 40 px limit | 53.2% | 2.7% |
| 3 of 5 frames, limit of 0.75 sides (chosen) | 53.2% | 2.4% |

The move limit was a fixed 40 px until 2026-11-16. Under simulated moderate shake on fdcl-gwu (`python -m testing.vibration_test --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL`, 43 px mean move), the detector finds 63.8% of markers:

| Move limit | Tracked | False IDs per 100 frames |
|------------|---------|--------------------------|
| 40 px | 32.6% | 0.2 |
| 80 px | 53.5% | 2.4 |
| None | 54.4% | 10.0 |
| 0.75 sides, at least 20 px (chosen) | 54.1% | 0.1 |

The two tables above were measured before the benchmark applied `MIN_SIDE_PX` and before `polygonalApproxAccuracyRate` returned to 0.03; the same `--track` command now gives `found=54.8% unmatched=0.8%`, with moderate shake raw 65.9% and tracked 57.2% (see `logs/DECISIONS.md`).

Scaling with marker size keeps nearly all the recall of no limit with no more wrong IDs than the fixed 40 px. Camera-motion compensation (KLT optical flow and `estimateAffinePartial2D`) was also tried as a prototype: it gave the same 54.1% but 3.2 false IDs per 100 frames, and cost 5.7 ms per frame on a PC, so it was not kept. That shake is a global affine move; real flights add rolling-shutter wobble and parallax.

Smoothing did not change these scores, because the benchmark accepts positions within 15 px, and it never changes which markers are reported. It does change where they are reported. The study in `analysis/smoothing/smoothing_study.ipynb` found that a weight of 0.6 left logged positions 15.2 px from the marker at moderate shake on fdcl-gwu, against 1.7 px at 1.0 (6.3 and 1.4 px on Shadow-ArUco), so smoothing was turned off on 2026-11-16. On a still scene, smoothing does steady the estimate of where a marker sits (14% at 0.6 on Shadow-ArUco), which is what centring needs. That filter belongs in `navigation`, where the drone's own motion is known, not in the logged positions. Confirming adds about 2 frames of delay, 67 ms at 30 frames per second. That footage uses another dictionary and was not filmed from a drone.

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
