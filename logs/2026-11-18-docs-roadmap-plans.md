# docs/roadmap-plans

**Agent:** Claude Code, Claude Fable 5.2
**Status:** ready for review

## Goal
Write a roadmap to the final and one plan per feature, after reviewing the code against the V1 rules. The loan kit ships soon, so its bring-up plan comes first.

## Steps
- 2026-11-18: Reviewed the docs, `detect.py` and `vehicle.py` against V1. No flight point can be scored today: nothing links detections to movement.
- 2026-11-18: Read ArduPilot's MTF-01, optical flow, precision landing, relay and Guided-mode pages for the values in the plans.
- 2026-11-18: Wrote `docs/plans/2026-11-18-roadmap.md` and 15 plans. Added a Roadmap section and two findings to `TODO.md`, and a link in both READMEs.

## Decisions
- The roadmap fixes the shared interfaces, so plans can be built separately.
- Landing is planned in Python first; ArduPilot's precision landing only if real landings miss 10 cm and the firmware has it.

## Verification
- `./scripts/check.sh`: all four checks pass. Docs only; no code changed.
- Unverified: every ArduPilot parameter value and MAVLink detail, on the kit. The plans mark each and name the test that settles it.

## Next Steps
- The project lead's decisions and the questions for the organisers, both listed in the roadmap.
