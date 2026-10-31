# Architecture

Each module owns one job. Modules that have not started hold only short READMEs.

| Module | Job | State |
|--------|-----|-------|
| `droneload/vision` | Reads cameras and recognises ArUco markers, target posters and floor lines | ArUco detection only |
| `droneload/flight` | Talks to the flight controller over MAVLink and holds its settings | Not started |
| `droneload/navigation` | Centres on targets, searches the field and crosses the window | Not started |
| `droneload/payload` | Grabs and releases the disc | Not started |
| `droneload/comms` | Talks to robot PULL-E and reads its replies | Not started |
| `droneload/mission` | Runs each challenge step by step and shows the jury what the drone detects | Not started |

`droneload/flight/stabilisation` holds flight controller settings and tuning. It is part of `flight`, not a separate module.

`testing/` holds tools that never run on the drone: the simulator setup, benchmark and test video generator. `tests/` holds automated tests, and `scripts/` holds setup and check scripts.

## Requirements

Each module's README lists its requirements, with a source:

- **2027 V0:** the first version of the 2027 rules. See `docs/contest-rules.md`.
- **2026 rules:** last year's rules, for details V0 leaves out.
- **Proposed:** a team target from the software plan, not a contest rule. The team can change it.

Update a requirement when its source changes.

## Dependencies

- `mission` calls the other modules. They do not call `mission`.
- `navigation` may use `vision` and `flight`.
- All other modules stay independent of each other.
- Only `flight` talks to the flight controller, and only `comms` talks to the robot.
