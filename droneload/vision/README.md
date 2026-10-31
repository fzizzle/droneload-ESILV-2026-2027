# vision

Reads the cameras and recognises what the drone needs to see: ArUco markers, target posters and floor lines.

**Status:** ArUco detection works on a PC, and logs each marker's centre in pixels. `pose.py` turns a detected marker into a position in metres, but it is tested only on simulated images and is not yet used by the detection loop. Posters, floor lines and live cameras are not done.

**Hardware:** the team must buy cameras, which are not chosen. The organisers provide a Qualcomm computer, exact model unconfirmed, so check the speed targets on the real board.

**Run it:** `python -m droneload.vision --source test_markers.mp4`. Options are in the main README.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Marker dictionary | 4x4, IDs 0-9 (`DICT_4X4_50` covers them) | 2027 V0 |
| Marker size | 20 × 20 cm | 2027 V0 |
| Show automatic detections on the organisers' screen during the run | Required | 2027 V0 |
| Recognise a delivery zone | 10 points, twice; −5 if done manually | 2027 V0 |
| Reject posters that are not targets | 2 to 4 decoy images, revealed at the final | 2027 V0 |
| Marker detection | 95% found with the right ID, on 100 photos from 0.5 to 3 m, tilted up to 45° | Proposed |
| Marker position | Offset in metres, using `solvePnP` and camera calibration | Proposed |
| Poster recognition | 98% of targets named, 95% of decoys rejected, under 200 ms per frame on the companion computer | Proposed |
| Camera capture | 30 frames per second, with no visible blur on a marker at 1.5 m in a hover | Proposed |
| Camera shutter | Global shutter, because vibration distorts rolling-shutter images | Proposed |
| Camera connection | USB (UVC) if the board is a Rubik Pi 3, because its listed CSI cameras are rolling shutter. Support for a specific camera is unverified | Proposed |
| Exposure | Fixed and short: start at 5 ms, and raise gain to compensate | Proposed |
| Camera mount | Soft-mounted, away from the motors, with cables that do not transmit vibration | Proposed |

## Measured So Far

| Test | Result | Note |
|------|--------|------|
| Shadow-ArUco `video_5` | 56.4% found, 26.6% of detections unmatched | Dark room and another dictionary, so not comparable with the 95% target |
| Generated test video | All 3 markers in all 150 frames | Easy footage; proves the program runs, not its quality |
| Detection time | About 3 ms per frame | On a PC at 1280 × 720, not on the drone |

The 95% target has not been tested, because no real `DICT_4X4_50` photo set exists yet.

## Position Accuracy

`marker_offset()` in `pose.py` uses OpenCV `solvePnP` and returns the marker's centre in metres from the camera: x right, y down, z forward. It needs a calibration file for the real camera.

Simulated with a 900 px focal length at 1280 × 720, 40 placements per distance, with no noise, blur or lens distortion:

| Distance | Mean error | Worst error |
|----------|------------|-------------|
| 1 m | 0.5 cm | 0.6 cm |
| 2 m | 2.1 cm | 2.3 cm |
| 3 m | 5.0 cm | 5.3 cm |
| 5 m | 13.4 cm | 14.8 cm |
| 8 m | 34.3 cm | 58.9 cm |

- Error grows quickly with distance, so close in before relying on a marker for landing or the window.
- The mean is close to the worst case, which suggests a consistent bias. Corner refinement may reduce it, but that changes detection, so it needs the benchmark.
- These are best-case numbers for this lens. Real accuracy depends on calibration and on the marker being printed at exactly 20 cm.

## Vibration

The organisers warn that camera vibration is usually a big problem. `python -m testing.vibration_test` simulates it on a clean generated image, with no real camera or drone. This table shows how often a marker was found:

| Marker side in image | Motion blur tolerated | 5 px wobble | 10 px wobble | 20 px wobble |
|----------------------|-----------------------|-------------|--------------|--------------|
| 60 px | 10 px (0% at 20 px) | 33% | 17% | 0% |
| 120 px | 20 px (25% at 30 px) | 58% | 0% | 0% |
| 240 px | 40 px or more | 100% | 100% | 8% |

- Blur is tolerated up to about one marker cell, which is a sixth of the marker's side. On a 20 cm marker, that is about 3 cm of movement during the exposure.
- Rolling-shutter wobble does much more damage than blur, especially on small markers, which is why this module proposes a global shutter.
- Real results will be worse, because real images have noise, tilt and uneven light. Measure on footage from a flying drone as soon as possible.

Software methods that reduce vibration's effects are planned in [`tracking/`](tracking/README.md).

## Risks

- Vibration blurs and distorts images. See Vibration above.
- The contest is indoors, but the venue's lighting is unknown.
- The previous team's detection worked on good-quality still images only.
- `ARUCO_LABELS` follows V0, so check it against each new version of the rules.
- The target images are not published. The 2027 theme is "Saveurs savantes".

## Uses

Nothing from other modules. `navigation` and `mission` use its results.
