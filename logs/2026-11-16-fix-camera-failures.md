# fix/camera-failures

**Agent:** Claude Code (Claude Sonnet, Claude Haiku)
**Status:** ready for review

## Goal
Handle camera failures in `detect.py`: reopen a live camera that stops sending frames, and reject an unknown `--dict` before the camera opens.

## Steps
- 2026-11-16: Added `REOPEN_AFTER_SEC`; a live camera is released and reopened after 2 s without frames, then every 2 s, one warning per attempt.
- 2026-11-16: `--dict` takes only `ARUCO_DICTS` (the `DICT_` names in `cv2.aruco`); an unknown name exits with code 2 before the camera opens.

## Decisions
- Reopen every 2 s, approved by the project lead.

## Verification
- `./scripts/check.sh` passes (4x [OK]).
- Reopening is tested with fake cameras only; it is unverified on hardware.
