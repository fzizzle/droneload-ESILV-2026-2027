# payload

Grabs the object and releases it over the target.

**Status:** Not started. The loan kit has no grabber, and one is not chosen: a servo claw, an electromagnet or an electromagnetic suction cup.

## Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Object | Round, 50 g at most, Ø40 mm ferrous disc, Ø62 mm ring | 2027 V0 |
| Drop scoring | 20 points automatic, 10 manual, twice | 2027 V0 |
| What counts as a hit | The object's first ground contact must be the target | 2027 V0 |
| Carrying an object through the window | 10 points automatic, 5 manual, twice | 2027 V0 |
| Drone mass | The grabber counts toward the 3 kg limit | 2027 V0 |
| Target size | A3 posters | 2027 V0 |
| Team's own objects | Allowed if similar in size and mass, and checked at qualification | 2027 V0 |
| Loading | The object is fitted by hand under the drone in zone A | 2027 V0 |
| After a miss | The team can return to zone A for another object | 2027 V0 |
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
