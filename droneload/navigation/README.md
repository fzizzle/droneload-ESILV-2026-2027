# navigation

Turns what the drone sees into movement: centring on targets, searching the field, following the safe path and crossing the window.

**Status:** Not started.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Search for a delivery zone | 30 points, twice | 2027 slides |
| Hold on the robot, following it unaided | 30 points automatic | 2027 slides |
| Follow the safe path | 30 points, twice; no obstacle within 50 cm of the line | 2027 slides |
| Window, outbound | 30 points automatic; 4 corner ArUcos | 2027 slides |
| Window, return | 50 points automatic; only 2 ArUcos | 2027 slides |
| Window while carrying an object | 10 points, twice | 2027 slides |
| Automatic round trip on the safe path | 30 points, with take-off and landing on zone A's ArUco | 2027 slides |
| Automatic round trip off the safe path | 70 points, same conditions | 2027 slides |
| Window size | 100 × 100 cm | 2027 slides |
| Arena | Mat of about 8 × 5 m in a 10 × 6 m cage, with obstacles up to the roof | 2027 slides |
| Landing on the take-off marker | Within 10 cm, 9 times in 10 | Proposed |
| Safe path | Follow a 5 m taped path both ways without leaving it | Proposed |
| Window crossing | 9 passes in 10 through a 1 × 1 m test frame | Proposed |

## Open Questions

- Line width and colours of the 2027 safe path are unknown. In 2026 it had a green line and a yellow line.
- Where the markers sit on the 2027 window is unknown.
- The drone needs a clearance margin in the window, so measure its width with propellers.

## Risks

- Crossing the window on the return is harder, because fewer markers are visible.
- Crossing with an object adds mass and may change the clearance.

## Uses

`vision` for targets and `flight` for movement.
