# Poster Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Name the four A3 target posters from the air, ignore the 2 to 4 decoys, and give each target's position so the drone can centre and drop on it. Per drop this is worth 60 points: search 30, recognise 10 and drop 20.

**Architecture:** The target images are not published, and the decoys appear only at the final, so nothing can be trained ahead. The recogniser therefore matches local image features against reference pictures loaded from a folder: adding a target means adding a file. A poster is flat, so a match is confirmed by fitting a homography and counting the features that agree. That fit also gives the poster's four corners, and from them its position in metres, exactly as for a marker.

**Tech Stack:** OpenCV (`SIFT_create`, `BFMatcher`, `findHomography`, all in the pinned wheel), numpy, pytest. No new dependency.

**Spec:** `docs/contest-rules.md`, Flight Test Part 1 and Open Questions; `droneload/vision/README.md` ("98% of targets named, 95% of decoys rejected, under 200 ms per frame on the companion computer").

## Global Constraints

- Needs `sim-camera` merged for the tests. The search and drop steps (Task 4) also need `centre-and-land` and `mission-runner`, and the drop needs `payload`.
- Reference folder: `targets/`, with `1.png` to `4.png` named after the target's number, and optionally `decoy-*.png`. Real references are not committed until the organisers publish annex 3; tests generate their own.
- A3 is 0.297 × 0.420 m. `POSTER_SIZE_M = (0.297, 0.420)` is a constant at the top of `posters.py`, with `FEATURES = "SIFT"`, `RATIO = 0.75`, `MIN_INLIERS = 15`, `MAX_FEATURES = 1500`, `DETECT_WIDTH = 960`.
- A poster the library does not know is never reported. A decoy in the library is reported with `is_target=False`, and no step ever drops on it.
- This is new detection, so the ArUco benchmarks need not run. Its own benchmark is Task 3.
- Branch `feature/poster-recognition`, log `logs/YYYY-MM-DD-feature-poster-recognition.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Two posters in one frame:** both are reported, each with its own corners. Test `test_two_posters_in_view` (Task 1).
2. **A poster seen upside down or sideways:** the drone approaches from any heading. Test `test_any_rotation` (Task 1).
3. **A decoy that resembles a target** (same theme, same colours): rejected by the inlier count, not by colour. Test `test_similar_decoy_is_rejected` (Task 1).
4. **A degenerate homography** (a few matches on one edge giving a sliver): rejected when the fitted outline is not convex or its sides are off the A3 ratio by more than 30%. Test `test_sliver_fit_is_rejected` (Task 1).
5. **An empty or missing `targets/` folder:** `PosterLibrary` raises at start, naming the folder, not at the first frame. Test `test_missing_targets_fail_at_start` (Task 1).

---

### Task 1: Recogniser

**Files:**
- Create: `droneload/vision/posters.py`
- Create: `testing/make_posters.py` (procedural stand-ins: random coloured shapes and large text on a white A3 page, seeded)
- Test: `tests/test_posters.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class Poster:
    name: str                 # "1" to "4", or the decoy's file stem
    is_target: bool
    corners: np.ndarray       # (4, 2) pixels: the reference image's corners in the frame
    cx: float
    cy: float
    inliers: int
    offset_m: tuple | None    # camera frame, as Marker.offset_m

class PosterLibrary:
    def __init__(self, folder="targets"): ...
    names: list

class PosterDetector:
    def __init__(self, library, calibration=None): ...
    def process(self, frame_bgr) -> list     # Posters, best first
```

`testing.make_posters.make_poster(seed, size_px=(600, 849)) -> np.ndarray`.

- [ ] **Step 1: Write the failing tests.** The library holds stand-ins for seeds 1 to 4; frames come from `sim_camera.paste_image` and `render_down`.

  - `test_names_the_poster_below`: poster 3 seen from 1.5 m is reported as `"3"`, a target, centred within 5 px of the image centre.
  - `test_offset_in_metres`: from 0.3 m south, `offset_m` is within 3 cm of `(0, -0.3, 1.5)`.
  - `test_two_posters_in_view`, `test_any_rotation` (0°, 90°, 180°, 270° and 37°), `test_similar_decoy_is_rejected` (a stand-in made with the same palette and another seed, not in the library, gives no report), `test_sliver_fit_is_rejected`, `test_missing_targets_fail_at_start`.
  - `test_known_decoy_is_marked`: a decoy in the library is reported with `is_target=False`.
  - `test_blank_floor_reports_nothing`.
  - `test_seen_from_two_metres`: named correctly at 2 m, the search height, where the poster is about 134 px wide.

- [ ] **Step 2: Run them and check they fail.** `python -m pytest tests/test_posters.py -q`.
- [ ] **Step 3: Implement.** Features for each reference are computed once in `PosterLibrary`. `process` resizes the frame to `DETECT_WIDTH`, matches against each reference with the ratio test, fits `findHomography` with RANSAC, applies the outline checks, and scales corners back to the frame. `offset_m` comes from `cv2.solvePnP` on the four corners with `POSTER_SIZE_M`.
- [ ] **Step 4: Run the tests.** Then render the poster from 2.5, 3 and 4 m and note in the log the furthest height at which it is still named; `SEARCH_HEIGHT_M` in Task 4 must stay under it.
- [ ] **Step 5: Commit.** Message "Recognise target posters by feature matching".

### Task 2: Command line and annotation

**Files:**
- Modify: `droneload/vision/detect.py` (`--targets FOLDER`; `annotate` draws poster outlines and names), `droneload/vision/posters.py`
- Test: `tests/test_posters.py`, `tests/test_detect.py`

**Interfaces:**
- Produces: `python -m droneload.vision --source SOURCE --targets targets/` outlines targets in green with their number and known decoys in grey. `annotate(frame, marker_frame, status="", posters=())`. **Posters are not written to `detections.csv`;** the CSV format does not change.

- [ ] **Step 1: Write the failing tests.** `test_annotate_draws_posters`, `test_csv_has_no_poster_rows`, `test_targets_option_reports_posters` (the terminal log names the poster).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh` and both ArUco benchmarks,** since `detect.py` changed. Expected: unchanged scores.
- [ ] **Step 5: Commit.** Message "Show recognised posters in the detection loop".

### Task 3: Poster benchmark

**Files:**
- Create: `testing/poster_test.py`
- Test: `tests/test_posters.py`
- Docs: `droneload/vision/README.md` (Status, Measured So Far), `README.md` and `README.fr.md` (Usage, Project Structure), `TODO.md` ("Poster and floor-line vision": tick the poster half)

**Interfaces:**
- Produces: `python -m testing.poster_test [--targets FOLDER] [--photos FOLDER]` prints one line: `views=N named=X% wrong=Y% decoys_rejected=Z% ms=T`. Without `--photos` it renders views itself: each target and 4 unknown decoys at 1, 1.5, 2 and 3 m, at 8 headings, with the shake levels from `testing.vibration_test`. With `--photos`, it scores real photos whose file names start with the poster's name or `decoy`.

- [ ] **Step 1: Write the failing test.** `test_poster_benchmark_line`: on clean rendered views the line reports `named=100.0%` and `decoys_rejected=100.0%`.
- [ ] **Step 2: Run it and check it fails.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run it at each shake level.** Log the results, and the time per frame on the PC. Add them to the `vision` README, marked as stand-in images.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Add a poster recognition benchmark".

### Task 4: Search and drop steps

Needs the project lead's OK: it steers a simulated drone.

**Files:**
- Create: `droneload/navigation/search.py`
- Modify: `droneload/navigation/centre.py`, `droneload/mission/runner.py` (`Context.posters`), `droneload/mission/plans.py`
- Test: `tests/test_navigation_search.py`
- Docs: `droneload/navigation/README.md`, `docs/mission-map.md`

**Interfaces:**
- Produces: `Context.posters: dict` (camera name to this tick's poster list). Steps `SearchForTarget(target=None, timeout_s=90)`, which flies a fixed sweep across zone C (`SWEEP_LEGS_M`, a constant list of forward and right moves) at `SEARCH_HEIGHT_M = 2.0` until the target named in `ctx.notes["target"]` is seen as a target, and `CentreOnTarget(timeout_s=30)`, which is `CentreOnMarker` fed by the poster's `offset_m`. The drop itself is `payload`'s step.
- **How `ctx.notes["target"]` is set is an open question for the organisers.** Until they answer, `python -m droneload.mission --target N` sets it before take-off, which the rules may count as a manual command.

- [ ] **Step 1: Write the failing tests.** `test_search_finds_the_target` (four posters along the far edge in the order 1, 3, 2, 4, as Figure 1 shows, and two decoys: the step ends with the named target in view), `test_search_passes_other_targets`, `test_search_times_out_without_the_target`, `test_centres_on_the_target` (ends within 5 cm of the poster's centre), `test_never_centres_on_a_decoy`.
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `./scripts/check.sh`.**
- [ ] **Step 5: Update the docs and commit.** Message "Search zone C for a target and centre on it".

## Done When

- [ ] `python -m testing.poster_test` meets 98% named and 95% of decoys rejected on stand-in images at moderate shake, or the log says how far it falls short and why.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- When annex 3 is published: print the four targets at A3, photograph them from 1 to 3 m, and rerun the benchmark with `--photos`. Glossy prints under hall lighting are the likely trouble.
- At the final: photograph each decoy as soon as it is revealed and add it to `targets/` as `decoy-N.png`. Rehearse this; there is little time.
- Measure the time per frame on the companion computer. If it is over 200 ms, switch `FEATURES` to `"ORB"` and rerun the benchmark.
