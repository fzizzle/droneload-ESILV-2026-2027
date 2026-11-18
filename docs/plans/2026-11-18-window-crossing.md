# Window Crossing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK before Task 3:** from there on, this code steers a simulated drone (`AGENTS.md`, Stop and Ask). It also needs the forward camera, which is not bought yet.

**Goal:** Fly through the 100 × 100 cm window in both directions. The window is worth up to 170 points (30 out, 50 back, 20 carrying an object, 70 for the round trip off the safe path) and is the crossing Mission 2 needs.

**Architecture:** The window's markers sit at known places around the opening, so all their corners together fix the window's position and facing in one `solvePnP` call, far more accurately than any single marker. The drone lines up on the window's axis at a standoff distance, where every marker is still in view, checks it is centred and square, then flies straight through on optical flow alone, because the markers leave the image as it gets close.

**Tech Stack:** OpenCV, numpy, pytest. No new dependency.

**Spec:** `docs/contest-rules.md`, Arena (zone E), ArUco Markers and Open Questions; `droneload/navigation/README.md` ("9 passes in 10 through a 1 × 1 m test frame").

## Global Constraints

- Needs these plans merged: `sim-camera`, `vision-api`, `flight-velocity`, `mission-runner`, `centre-and-land`.
- **The marker positions are not published.** They are constants at the top of `droneload/vision/window.py`, as metres from the opening's centre (x right, y up, seen from the side the markers face), and are labelled guesses until measured on the real window:

```python
WINDOW_FRONT = {4: (0.65, -0.35), 5: (0.65, 0.35), 6: (-0.65, 0.35), 7: (-0.65, -0.35)}   # A to C side
WINDOW_BACK  = {8: (0.20, -0.60), 9: (0.20, 0.60)}                                         # C to A side
```

- **Clearance.** An F450 with 9.45-inch propellers is about 0.56 m across, which leaves about 0.22 m each side. Measure the real width with propellers and the grabber, and set `DRONE_WIDTH_M`. The tolerances below come from it.
- Settings, at the top of `droneload/navigation/window.py`: `STANDOFF_M = 2.0`, `ALIGN_TOLERANCE_M = 0.05`, `ALIGN_YAW_RAD = 0.05`, `ALIGN_HOLD_S = 1.0`, `CROSS_SPEED_MPS = 0.4`, `CROSS_DISTANCE_M = STANDOFF_M + 1.5`, `SEARCH_CLIMB_MPS = 0.2`, `MAX_WINDOW_HEIGHT_M = 2.5`.
- Every layout marker must fit in the image at `STANDOFF_M`. With the simulated camera (900 px focal length at 1280 × 720) and the guessed layouts, 2.0 m is the closest that fits the back side. Recompute it for the chosen forward camera.
- The crossing is blind for about 9 s. It is only started from a pose that passed the alignment check, and it is not corrected sideways on the way.
- The window's height is random. The search climbs until the markers are in view; the rangefinder's ceiling (8 m) and the cage's roof bound it.
- **Risk to measure on the drone:** passing over the window's lower bar changes the rangefinder's reading suddenly, which may disturb the optical flow estimate. Height comes from the barometer (`EK3_SRC1_POSZ = 1`), but flow scales with range.
- Branch `feature/window-crossing`, log `logs/YYYY-MM-DD-feature-window-crossing.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Only some markers in view:** one marker still gives a pose, with `markers_used` reported; the alignment check demands at least 2, so a single marker can guide the approach but not start the crossing. Test `test_alignment_needs_two_markers` (Task 3).
2. **Markers from the wrong side:** seeing 8 or 9 while expecting the front, or 4 to 7 while expecting the back, fails the step with a message, rather than crossing a window the drone is already behind. Test `test_wrong_side_fails` (Task 3).
3. **A marker printed at the wrong size or misplaced:** the combined fit's reprojection error rises. Above `MAX_REPROJECTION_PX = 3.0` no pose is returned. Test `test_bad_layout_is_rejected` (Task 1).
4. **Approaching at an angle:** the drone moves sideways onto the window's axis and yaws square before the check can pass. Test `test_aligns_from_an_angle` (Task 3).
5. **Markers lost during alignment:** stop, and fail after `LOST_AFTER_S`. **Lost during the crossing:** expected. Test `test_markers_lost_while_aligning_fails` (Task 3).

---

### Task 1: Window pose from its markers

**Files:**
- Create: `droneload/vision/window.py`
- Test: `tests/test_window.py`

**Interfaces:**
- Consumes: `Marker.corners`.
- Produces:

```python
@dataclass(frozen=True)
class WindowPose:
    centre: tuple            # the opening's centre, camera frame, metres
    yaw_rad: float           # the window's facing relative to the camera's axis; 0 when square on
    markers_used: int
    error_px: float          # mean reprojection error

def locate_window(markers, layout, camera_matrix, dist_coeffs, marker_m=0.20) -> WindowPose | None
```

- [ ] **Step 1: Write the failing tests.** Project the layout's marker corners through a known camera pose with `cv2.projectPoints` and build `Marker` objects from them.

  - `test_square_on_at_two_metres`: `centre` within 2 cm of `(0, 0, 2.0)`, `yaw_rad` within 0.01 of 0, `markers_used == 4`.
  - `test_offset_and_angle`: from 0.4 m right, 0.2 m low and 20° off square, the pose is within 3 cm and 0.02 rad.
  - `test_back_side_with_two_markers`: with `WINDOW_BACK`, the centre is within 3 cm although both markers are 0.20 m off-centre.
  - `test_one_marker_still_gives_a_pose`: within 10 cm, `markers_used == 1`.
  - `test_pixel_noise`: with 0.5 px of noise on every corner, 4 markers at 2 m give a centre within 3 cm in 50 trials of 50.
  - `test_bad_layout_is_rejected`: one marker shifted 10 cm from its layout position gives `None`.
  - `test_no_layout_marker_gives_none`: markers 0 and 1 only.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_window.py -q`.
- [ ] **Step 3: Implement** with one `cv2.solvePnP` over every visible layout marker's four corners (`SOLVEPNP_IPPE` needs coplanar points, which these are), then `cv2.projectPoints` for the error.
- [ ] **Step 4: Run the tests.** Note in the log the pose error at 2, 3 and 4 m with 0.5 px of noise; the approach starts from where it drops under 5 cm.
- [ ] **Step 5: Commit.** Message "Locate the window from its markers".

### Task 2: A simulated forward camera

**Files:**
- Modify: `testing/sim_camera.py`
- Test: `tests/test_sim_camera.py`

**Interfaces:**
- Produces: `render_forward(walls, north, east, height, yaw=0.0, roll=0.0, pitch=0.0, camera_matrix=CAMERA_MATRIX, size=SIZE) -> np.ndarray`, where `walls` is a list of `Wall(image, px_per_m, north, east, bottom_m, facing_rad)`: upright flat images. `make_window_wall(layout, north, east, sill_m, facing_rad) -> Wall` draws the layout's markers around a 1 × 1 m opening. `SimCamera` gains `mount="down"` or `"forward"`.

- [ ] **Step 1: Write the failing tests.** `test_window_seen_square_on` (from 2 m, all four markers are detected, and `locate_window` gives the centre within 3 cm), `test_window_seen_from_behind_is_not_drawn` (a wall facing away shows nothing), `test_window_height_follows_the_sill`.
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.** Each wall is one homography, built as `render_down` builds the floor's, with the wall's plane in place of the floor's and the mount `[[0, 0, 1], [1, 0, 0], [0, 1, 0]]`.
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Simulate a forward camera looking at upright surfaces".

### Task 3: The crossing

**Files:**
- Create: `droneload/navigation/window.py`
- Modify: `droneload/mission/plans.py`
- Test: `tests/test_navigation_window.py`, `tests/test_mission_sitl.py`
- Docs: `droneload/navigation/README.md` (Status, measured results), `droneload/vision/README.md`, `docs/mission-map.md` (statuses), `README.md` and `README.fr.md` (Status)

**Interfaces:**
- Consumes: `locate_window`, `frames.level_offset` with `FORWARD_CAMERA`, `Centring`, `Context`.
- `Turn` comes from `docs/plans/2026-11-18-safe-path.md`, Task 3. If that plan is not merged, add `Turn` here as it is specified there.
- Produces: step `CrossWindow(side="front", timeout_s=120)`, with `side="back"` for the return. Phases: **search**, climbing at `SEARCH_CLIMB_MPS` from the current height while yawing ±30° until a layout marker is confirmed; **align**, steering to the point `STANDOFF_M` in front of the opening's centre on its axis, at its height, yawed square; **check**, holding within `ALIGN_TOLERANCE_M` and `ALIGN_YAW_RAD` with at least 2 markers for `ALIGN_HOLD_S`; **cross**, flying forward `CROSS_DISTANCE_M` at `CROSS_SPEED_MPS`, measured from `vehicle.position`, with zero sideways and vertical velocity; **done**. Plan `"part2-window"`:

```python
[Arm(), TakeOff(1.0), CrossWindow("front"), Hover(5), Turn(math.pi),
 CrossWindow("back"), CentreOnMarker(0), LandOnMarker(0)]
```

- [ ] **Step 1: Write the failing tests,** closed loop with `KinematicVehicle` and a forward `SimCamera`. The test records the vehicle's position as it passes the wall's plane.

  - `test_crosses_through_the_centre`: starting 3 m in front and square on, it passes the plane within 10 cm of the opening's centre, in both axes.
  - `test_aligns_from_an_angle`: starting 3 m away, 1 m to the side and 25° off, the same.
  - `test_finds_a_high_window`: with the sill at 1.5 m and the drone at 1.0 m, it climbs and crosses.
  - `test_crosses_back_with_two_markers`: `side="back"` with the `WINDOW_BACK` layout passes within 10 cm.
  - `test_ten_crossings`: 10 starts spread over ±1 m, ±20° and sills from 0.5 to 1.5 m, with `drift_mps` of 0.03 m/s in a different direction each run: all pass within `0.5 − DRONE_WIDTH_M / 2 − 0.05` m of the centre.
  - `test_alignment_needs_two_markers`, `test_wrong_side_fails`, `test_markers_lost_while_aligning_fails`: as in Review Focus.
  - `test_window_above_the_limit_fails`: no marker found by `MAX_WINDOW_HEIGHT_M` fails the step.
  - Opt-in simulator test `test_part2_window_in_the_simulator`.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and the simulator tests.** Log the crossing error and the simulator's drift over the blind stretch.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Cross the window in both directions".

## Done When

- [ ] `python -m droneload.mission --plan part2-window` completes in the ArduPilot simulator.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- Build a 1 × 1 m test frame from light tube or cardboard, with printed markers. Light, so a touch does not break the drone: the rules give up to 40 points for crash resistance, and propeller guards help both.
- Before any flight through it: carry the drone through by hand, motors off, with the program running, and check the alignment check and the display agree with a tape measure.
- Measure the flow drift over 3.5 m of blind flight on the drone. If it exceeds 10 cm, shorten `STANDOFF_M`.
- Ask the organisers for the marker positions, and replace the guessed layouts.
