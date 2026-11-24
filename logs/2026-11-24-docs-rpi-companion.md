# docs/rpi-companion

**Agent:** Claude Code (Claude Opus 5.5)
**Status:** ready for review

## Goal
Record that a Raspberry Pi 5 is tested first, then the lent Qualcomm computer, list the Pi work, and record the first camera.

## Steps
- 2026-11-24: Updated `AGENTS.md` context, added the decision to `DECISIONS.md`, and added a Raspberry Pi 5 section and a regulator item to `TODO.md`.
- 2026-11-24: Compared global-shutter cameras on a €200 budget; recorded the first camera in `DECISIONS.md` and `TODO.md`.

## Decisions
- The organisers accept any computer; the flight computer is chosen after testing both (project lead).
- First camera: Svpro/ELP USBGS1200P01 board, 126° lens, over the OV9782 (70° too narrow), Arducam AR0234 USB 3 (over budget for two), Pi GS camera (Pi only) and IMX415 4K (rolling shutter).

## Verification
- `./scripts/check.sh`: shell syntax, shellcheck, ruff and pytest OK. Docs only; nothing run on a Pi.

## Next Steps
- `feature/rpi-camera` (driver fixes, `picamera:N`, tests) and a Pi setup script with README sections.
