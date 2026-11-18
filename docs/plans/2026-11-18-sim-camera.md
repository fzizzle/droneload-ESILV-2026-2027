# Simulated Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give tests a downward camera that shows what the drone would see from any position over the arena floor, so landing, path following and search can be tested in a closed loop on a PC.

**Architecture:** The floor is one flat image with a known scale. A downward camera over a flat floor sees a perspective warp of that image, so each frame is one `cv2.warpPerspective` call computed from the drone's position, height and attitude. `SimCamera` wraps this with `open()`, `read()` and `release()`, so the rest of the code cannot tell it from a real camera.

**Tech Stack:** OpenCV, numpy, pytest. No new dependency. Everything lives in `testing/`, which never runs on the drone.

**Spec:** `docs/plans/2026-11-18-roadmap.md`, "Shared Interfaces".

## Global Constraints

- Frames are as the roadmap defines them. Floor points are (north, east) in metres, in the local frame.
- The downward camera is mounted with the top of the image toward the drone's front: camera x is body right, camera y is body back, camera z is body down.
- Default intrinsics match the `vision` README's accuracy table: focal length 900 px at 1280 × 720, principal point at the centre, no distortion.
- Floor scale `PX_PER_M = 200`, so a 20 cm marker is 40 px in the floor image.
- No file in `droneload/` imports from `testing/`.
- Branch `feature/sim-camera`, log `logs/YYYY-MM-DD-feature-sim-camera.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Camera partly or wholly off the floor image:** the frame must fill the outside with `FLOOR_COLOUR`, not crash or wrap. Test `test_view_off_the_floor_is_plain` (Task 1).
2. **Yaw sign:** turning the drone clockwise seen from above must turn the image anticlockwise. Test `test_yaw_turns_the_view` (Task 1).
3. **Tilt:** rolling right points the camera left, so a marker below the drone must move right in the image by `900 × tan(roll)` px. Test `test_roll_shifts_the_marker` (Task 1). Navigation's tilt compensation relies on this being right.
4. **Height near zero:** at 0.05 m the warp must still return a frame, since a landing ends there. Test `test_view_just_above_the_floor` (Task 1).
5. **A pose source that returns `None`** (the vehicle has no position yet): `read()` returns `(False, None)`. Test `test_read_without_a_pose` (Task 2).

---

### Task 1: Floor and renderer

**Files:**
- Create: `testing/sim_camera.py`
- Test: `tests/test_sim_camera.py`

**Interfaces:**
- Produces:

```python
PX_PER_M     = 200
FLOOR_COLOUR = (200, 200, 200)
SIZE         = (1280, 720)
CAMERA_MATRIX = np.array([[900, 0, 640], [0, 900, 360], [0, 0, 1]], dtype=np.float64)

@dataclass
class Floor:
    image: np.ndarray          # BGR; north is up, east is right
    origin_px: tuple           # (x, y) pixel of local (0, 0)
    px_per_m: float = PX_PER_M

def make_floor(markers, size_m=(8.0, 5.0), dict_name="DICT_4X4_50", marker_m=0.20) -> Floor
#   markers: {id: (north_m, east_m)} or {id: (north_m, east_m, yaw_rad)}; size_m is (north, east);
#   local (0, 0) is the floor's south-west corner.

def render_down(floor, north, east, height, yaw=0.0, roll=0.0, pitch=0.0,
                camera_matrix=CAMERA_MATRIX, size=SIZE) -> np.ndarray
```

- [ ] **Step 1: Write the failing tests** in `tests/test_sim_camera.py`. Each builds `make_floor({0: (4.0, 2.5)})`, renders, and runs `detect.make_detector().detectMarkers` on the grey frame:

  - `test_marker_below_is_centred`: at `(4.0, 2.5)`, height 1.5, the marker's centre is within 2 px of `(640, 360)` and its side is `900 × 0.20 / 1.5 = 120` px ± 2.
  - `test_pose_matches_height`: `pose.marker_offset(corner, CAMERA_MATRIX, np.zeros(5))` gives `z` within 2 cm of 1.5 and `x`, `y` within 1 cm of 0.
  - `test_marker_ahead_is_higher`: at `(3.7, 2.5)` the marker's centre has `cy = 360 − 900 × 0.3 / 1.5 = 180` ± 3 and `cx = 640` ± 3.
  - `test_marker_to_the_right`: at `(4.0, 2.2)` the centre has `cx = 820` ± 3.
  - `test_yaw_turns_the_view`: at `(3.7, 2.5)` with `yaw = π/2` (facing east), the marker, which is north, appears on the left: `cx = 460` ± 3, `cy = 360` ± 3.
  - `test_roll_shifts_the_marker`: over the marker with `roll = radians(5)`, `cx = 640 + 900 × tan(5°)` ± 3, which is about 719, and `cy = 360` ± 3.
  - `test_view_off_the_floor_is_plain`: at `(-20, -20)` every pixel equals `FLOOR_COLOUR`.
  - `test_view_just_above_the_floor`: at height 0.05 the frame has shape `(720, 1280, 3)`.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_sim_camera.py -q`. Expected: import error.

- [ ] **Step 3: Implement `Floor`, `make_floor` and `render_down`.** The warp is determined as follows. With `R_wb` the body-to-local rotation from yaw, pitch and roll (ZYX order) and `R_bc` the camera-to-body rotation `[[0, -1, 0], [1, 0, 0], [0, 0, 1]]`, the local-to-camera rotation is `R = (R_wb @ R_bc).T`. The camera sits at `C = (north, east, -height)`. A floor point `(n, e, 0)` projects to `K @ R @ ((n, e, 0) − C)`, so the floor-metres-to-pixel homography is `H = K @ [r1, r2, −R @ C]`, with `r1` and `r2` the first two columns of `R`. Compose it with the floor-image-pixel-to-metres transform, and pass the result to `cv2.warpPerspective` with `borderValue=FLOOR_COLOUR`.

- [ ] **Step 4: Run the tests.** Expected: all pass.

- [ ] **Step 5: Commit.** `git add testing/sim_camera.py tests/test_sim_camera.py`, message "Add a simulated downward camera over a flat floor".

### Task 2: `SimCamera` and floor drawing helpers

**Files:**
- Modify: `testing/sim_camera.py`
- Test: `tests/test_sim_camera.py`
- Docs: `README.md` and `README.fr.md` (Project Structure: one line for `sim_camera.py`), `docs/architecture.md` (the `testing/` sentence)

**Interfaces:**
- Consumes: `Floor`, `render_down` from Task 1.
- Produces:

```python
class SimCamera:
    finite = False
    def __init__(self, floor, pose, camera_matrix=CAMERA_MATRIX, size=SIZE): ...
    #   pose: a function returning (north, east, height, yaw, roll, pitch), or None when unknown
    def open(self) -> bool
    def read(self) -> tuple          # (True, frame) or (False, None)
    def release(self) -> None

def vehicle_pose(vehicle):           # for SimCamera(pose=lambda: vehicle_pose(v))
    """(north, east, height, yaw, roll, pitch) from vehicle.position and vehicle.attitude, or None."""

def draw_line(floor, points_m, colour_bgr, width_m=0.05) -> None    # a polyline through (north, east) points
def paste_image(floor, image_bgr, north, east, width_m, yaw=0.0) -> None   # a poster, centred there
```

- [ ] **Step 1: Write the failing tests.**

  - `test_sim_camera_reads_like_a_camera`: `open()` is true, `read()` returns `(True, frame)` with the marker centred for a fixed pose, and `read()` after `release()` returns `(False, None)`.
  - `test_read_without_a_pose`: with `pose=lambda: None`, `read()` returns `(False, None)`.
  - `test_vehicle_pose`: an object with `position = (1.0, 2.0, -1.5)` and `attitude = (0.1, 0.2, 0.3)` gives `(1.0, 2.0, 1.5, 0.3, 0.1, 0.2)`; with `position = None` it gives `None`.
  - `test_draw_line_is_seen`: a green line drawn north through `(0..8, 2.5)` and rendered from `(4.0, 2.5)` at 1.5 m has green pixels in column 640 of every row.
  - `test_paste_image`: a 0.297 m wide all-red image pasted at `(4.0, 2.5)` and rendered from above at 1.5 m is red at `(640, 360)` and spans about `900 × 0.297 / 1.5 = 178` px ± 4 in width.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement the four additions.** `draw_line` uses `cv2.polylines` with the width converted to floor pixels; `paste_image` uses `cv2.warpAffine` into the floor image.
- [ ] **Step 4: Run `./scripts/check.sh`.** Expected: four `[OK]` lines.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Add SimCamera and floor drawing helpers".

## Done When

- [ ] A test can place markers, lines and posters on a floor and read frames from any pose.
- [ ] `./scripts/check.sh` passes, and the pull request is open.

## Not in This Plan

- Upright surfaces, for the window. `docs/plans/2026-11-18-window-crossing.md` adds them.
- Blur, noise and lens distortion. `testing/vibration_test.py` already applies shake to frames; combine them only when a test needs it.
