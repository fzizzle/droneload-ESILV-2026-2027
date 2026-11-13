# feature/show-record

**Agent:** Claude Code, Opus 5.5
**Status:** ready for review

## Goal
Let people watch detection and tracking: `--show` opens a window, `--record FILE` saves an annotated video.

## Steps
- 2026-11-13: Overlay: confirmed markers green with ID, unconfirmed grey, status bar with detect ms, fps and counts.
- 2026-11-13: `--show` and `--record`, with 4 new tests.
- 2026-11-13: Swapped the headless OpenCV wheel for the GUI one (approved).
- 2026-11-13: Recorded Shadow-ArUco `video_5`: 1334 frames at 800 × 600, overlay checked on a frame.

## Decisions
- The status bar is also drawn on `aruco_debug.jpg` and recordings, which serve the jury display.

## Verification
- `./scripts/check.sh` passes. The `--show` window was not opened in a test; it is mocked. Not checked on the board, which uses its own OpenCV build.

## Next Steps
- Decide how the display reaches the organisers' screen.
