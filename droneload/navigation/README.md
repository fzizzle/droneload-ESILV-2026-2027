# navigation

Turns what the drone sees into movement: centring on targets, searching the field, following the safe path and crossing the window.

**Status:** Not started.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Search for a delivery zone | 30 points, twice | 2027 V0 |
| Hold on the robot, following it unaided | 30 points automatic | 2027 V0 |
| Follow the safe path | 30 points, twice; no obstacle within 50 cm of the line | 2027 V0 |
| Window, outbound | 30 points automatic; 4 corner ArUcos | 2027 V0 |
| Window, return | 50 points automatic; only 2 ArUcos | 2027 V0 |
| Window while carrying an object | 10 points, twice | 2027 V0 |
| Automatic round trip on the safe path | 30 points, with take-off and landing on zone A's ArUco | 2027 V0 |
| Automatic round trip off the safe path | 70 points, same conditions | 2027 V0 |
| Window | 100 × 100 cm, at a random height | 2027 V0 |
| Arena | Mat of about 8 × 5 m in a 10 × 6 m cage, with obstacles up to the roof | 2027 V0 |
| Landing on the take-off marker | Within 10 cm, 9 times in 10 | Proposed |
| Safe path | Follow a 5 m taped path both ways without leaving it | Proposed |
| Window crossing | 9 passes in 10 through a 1 × 1 m test frame | Proposed |

## Open Questions

- The safe path has a green line on the right and a yellow line on the left, seen from the pilot station. Line width and exact colours are unknown.
- Window markers are off the diagonals on one side and off-centre on the other. Exact positions are unknown.
- The drone needs a clearance margin in the window, so measure its width with propellers.

## Risks

- Crossing the window on the return is harder, because fewer markers are visible.
- Crossing with an object adds mass and may change the clearance.

## Uses

`vision` for targets and `flight` for movement.
