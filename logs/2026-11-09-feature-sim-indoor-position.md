# feature/sim-indoor-position

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Fly the simulator without GPS, on optical flow and a rangefinder, to match the loan kit.

## Steps
- 2026-11-09: Arming failed with "Need Position Estimate": no origin without GPS, and the 0 m ground reading was below `RNGFND1_MIN`. Fixed both.
- 2026-11-09: A Paris origin failed the compass check, so `ORIGIN` is the simulator's home; `set_origin()` retries. The test checks the true position: 1.10 m moved, 1.05 m estimated.

## Decisions
- Estimator settings go in `flight/stabilisation/`, simulated sensors in `testing/`, so no simulator driver reaches a drone.

## Verification
- `./scripts/check.sh` passed. Simulator tests passed in 16 s. Not tested on a drone.

## Next Steps
- Simulate beacons, set the venue origin, and set real sensor drivers. See `TODO.md`.
