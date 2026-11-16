# fix/camera-failures

**Agent:** Claude Code (Claude Sonnet)
**Status:** in progress

## Goal
Handle camera failures in `detect.py`: reopen a live camera that stops sending frames, and reject an unknown `--dict` before the camera opens.

## Steps
- 2026-11-16: Added `REOPEN_AFTER_SEC`; a live camera is released and reopened after 2 s without frames, then every 2 s, one warning per attempt.

## Decisions
- Reopen every 2 s, approved by the project lead.

## Verification
- `./scripts/check.sh` result recorded in the pull request.
- Reopening is tested with fake cameras only; it is unverified on hardware.

## Next Steps
- Reject an unknown `--dict` before the camera opens.
