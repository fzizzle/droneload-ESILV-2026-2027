# feature/flight-watchdog

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Stop the drone if the mission program stops, as a safety net before more simulator work.

## Steps
- 2026-11-09: `Vehicle` sends 1 Hz heartbeats and refuses to arm unless `FS_GCS_ENABLE` is set. `failsafe.parm` lands after 3 s without one; `sim.sh` loads it.
- 2026-11-09: Split the simulator test into demo, takeover and failsafe tests. First run failed: at 5x speed-up, heartbeats were 5 s apart in sim time, so the test now scales the period.

## Decisions
- Use ArduPilot's GCS failsafe instead of sending zero velocity from Python: it still works if the program crashes.

## Verification
- `./scripts/check.sh` passed. Simulator tests passed in 19 s; the failsafe test fails with `FS_GCS_TIMEOUT 60`. Not tested on a Pixhawk.

## Next Steps
- Check the failsafe on the Pixhawk with propellers off.
