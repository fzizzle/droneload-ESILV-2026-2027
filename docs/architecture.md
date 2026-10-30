# Architecture

Each module owns one job. Modules that have not started hold only a short `README.md`.

| Module | Job | State |
|--------|-----|-------|
| `droneload/vision` | Reads cameras and recognises ArUco markers, target posters and floor lines | ArUco detection only |
| `droneload/flight` | Talks to the flight controller over MAVLink and holds its settings | Not started |
| `droneload/navigation` | Centres on targets, searches the field and crosses the window | Not started |
| `droneload/payload` | Grabs and releases the disc | Not started |
| `droneload/comms` | Talks to robot PULL-E and reads its replies | Not started |
| `droneload/mission` | Runs each challenge step by step and shows the jury what the drone detects | Not started |

`testing/` holds tools that never run on the drone: the simulator setup, benchmark and test video generator. `tests/` holds automated tests, and `scripts/` holds setup and check scripts.

## Dependencies

- `mission` calls the other modules. They do not call `mission`.
- `navigation` may use `vision` and `flight`.
- All other modules stay independent of each other.
- Only `flight` talks to the flight controller, and only `comms` talks to the robot.
