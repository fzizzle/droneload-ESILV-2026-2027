# docs/rpi-companion

**Agent:** Claude Code (Claude Opus 5.5)
**Status:** ready for review

## Goal
Record that a Raspberry Pi 5 is tested first, then the lent Qualcomm computer, and list the Pi work.

## Steps
- 2026-11-24: Updated `AGENTS.md` context, added the decision to `DECISIONS.md`, and added a Raspberry Pi 5 section and a regulator item to `TODO.md`.

## Decisions
- The organisers accept any computer; the flight computer is chosen after testing both (project lead).

## Verification
- `./scripts/check.sh`: shell syntax, shellcheck, ruff and pytest OK. Docs only; nothing run on a Pi.

## Next Steps
- `feature/rpi-camera` (driver fixes, `picamera:N`, tests) and a Pi setup script with README sections.
