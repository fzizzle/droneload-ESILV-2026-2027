# mission

Runs the contest run step by step, decides what happens next, and shows the jury what the drone detects.

**Status:** Not started.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Run length | One 15-minute run, from motor start to propeller stop | 2027 slides |
| Battery swaps and repairs | Count against the clock, except an exceptional repair | 2027 slides |
| Automatic flight points | 670 maximum; a manual-only run scores 40 at most | 2027 slides |
| Full automatic mission | 100 points, twice, with different tasks | 2027 slides |
| What a full mission includes | Take-off to landing in A, one Part 1 task and one Part 2 task | 2027 slides |
| Operator input during automatic flight | Only confirming that an action has finished; any other command makes it manual | 2026 rules |
| Detection display | Shown on the organisers' screen during the run | 2026 rules |
| Every step | Has a timeout and a way out to landing | Proposed |
| Display delay | Under half a second on a laptop | Proposed |

## Done When

- A full run completes in simulation.
- Every abort path ends in a landing: target lost, low battery and pilot takeover.
- Each state change is logged.

## Open Questions

- How does the drone learn the referee's target? In 2026, choosing the target counted as a manual command.
- May the ground station use Wi-Fi at the venue?

## Risks

- Fifteen minutes must cover both missions, so measure how long each step takes.
- The safety kill switch stays on the transmitter. A screen button is never the safety stop.

## Uses

All other modules. Nothing depends on this module.
