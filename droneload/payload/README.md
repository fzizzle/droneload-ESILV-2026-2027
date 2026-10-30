# payload

Grabs the object and releases it over the target.

**Status:** Not started. The loan kit has no grabber, and one is not chosen: a servo claw, an electromagnet or an electromagnetic suction cup.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Object | Round, 50 g at most, Ø40 mm ferrous disc, Ø62 mm ring | 2027 slides |
| Drop scoring | 20 points automatic, 10 manual, twice | 2027 slides |
| What counts as a hit | The object's first ground contact must be the target | 2027 slides |
| Carrying an object through the window | 10 points automatic, 5 manual, twice | 2027 slides |
| Drone mass | The grabber counts toward the 3 kg limit | 2027 slides |
| Target size | A3 posters | 2026 rules |
| Object may be swapped | Teams could bring similar objects if inspected | 2026 rules |
| Drop accuracy | Measure 20 drops each from 0.5, 1 and 1.5 m onto an A3 sheet, and record the hit rate | Proposed |

There is no agreed hit-rate target yet. Choose one after the drop test.

## Done When

- `grab()` and `release()` work on the bench, with propellers off.
- The hit rate at the chosen drop height is written down.

## Risks

- The object must not fall during flight or a window crossing. Test the grip before flying.
- An electromagnet needs power to hold, which uses battery and adds wiring.
- The previous team's claw parts are missing from the inventory.

## Uses

`flight`, if the grabber is driven by a flight controller output.
