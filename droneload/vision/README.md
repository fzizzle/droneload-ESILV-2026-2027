# vision

Reads the cameras and recognises what the drone needs to see: ArUco markers, target posters and floor lines.

**Status:** ArUco detection works on a PC, and logs each marker's centre in pixels. Pose, posters, floor lines and live cameras are not done.

**Run it:** `python -m droneload.vision --source test_markers.mp4`. Options are in the main README.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Marker dictionary | 4x4, IDs 0-15 (`DICT_4X4_50` covers them) | 2026 rules |
| Marker size | 20 × 20 cm | 2026 rules |
| Show automatic detections on the organisers' screen during the run | Required | 2026 rules |
| Recognise a delivery zone | 10 points, twice; −5 if done manually | 2027 slides |
| Reject posters that are not targets | Four decoys appeared on the day in 2026 | 2026 rules |
| Marker detection | 95% found with the right ID, on 100 photos from 0.5 to 3 m, tilted up to 45° | Proposed |
| Marker position | Offset in metres, using `solvePnP` and camera calibration | Proposed |
| Poster recognition | 98% of targets named, 95% of decoys rejected, under 200 ms per frame on the companion computer | Proposed |
| Camera capture | 30 frames per second, with no visible blur on a marker at 1.5 m in a hover | Proposed |

## Measured So Far

| Test | Result | Note |
|------|--------|------|
| Shadow-ArUco `video_5` | 56.4% found, 26.6% of detections unmatched | Dark room and another dictionary, so not comparable with the 95% target |
| Generated test video | All 3 markers in all 150 frames | Easy footage; proves the program runs, not its quality |
| Detection time | About 3 ms per frame | On a PC at 1280 × 720, not on the drone |

The 95% target has not been tested, because no real `DICT_4X4_50` photo set exists yet.

## Risks

- Vibration blurs images. The organisers warned about this, so plan short exposure and camera damping.
- Lighting may vary: the 2026 drop test ran in an outdoor cage.
- The previous team's detection worked on good-quality still images only.
- The 2027 marker IDs are not published, so `ARUCO_LABELS` may change.
- The 2027 target posters are not known yet.

## Uses

Nothing from other modules. `navigation` and `mission` use its results.
