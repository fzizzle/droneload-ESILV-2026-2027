# Tracker Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the tracker discarding shaken markers the detector still finds. Replace the fixed 40 px jump gate with one that scales with marker size, and measure how far logged positions lag under shake.

**Architecture:** Detections passed to `MarkerTracker.update` gain a fourth field, the marker's shortest side in px. Each track stores the side of its last accepted detection. The gate becomes `max(MIN_GATE_PX, GATE_SIDES × side) × since_hit`. `testing/vibration_test.py` learns the exact shake transform per frame, so it can report position error for raw and tracked output. Smoothing changes only after a person's decision (Task 3).

**Tech Stack:** Python standard library, OpenCV, numpy, pytest. No new dependency.

**Spec:** `docs/research/vibration-and-blur.md`, rows 1 and 2 of "What to try, in order", with the prototype results below.

## Prototype Results (2026-11-16, before planning)

These results come from throwaway scripts that monkeypatched the tracker. Nothing was committed. Vibration test on fdcl-gwu at moderate shake with `DICT_ARUCO_ORIGINAL`, plus `benchmark --track` on Shadow-ArUco `video_5`:

| Gate | moderate tracked | false IDs/100 frames | bench found | bench unmatched |
|---|---|---|---|---|
| 40 px (current) | 32.6% | 0.2 | 53.2% | 2.7% |
| 80 px | 53.5% | 2.4 | 53.2% | 3.3% |
| 120 px | 54.1% | 3.5 | 53.2% | 4.0% |
| none | 54.4% | 10.0 | 53.1% | 6.6% |
| **max(20, 0.75 × side), track's side** | **54.1%** | **0.1** | **53.2%** | **2.4%** |
| 40 px + KLT camera-motion compensation | 54.1% | 3.2 | 52.9% | 2.8% |

- The size-scaled gate matches the no-gate recall and beats the current gate on false IDs and unmatched rate. Marker sides: fdcl-gwu median 144 px, Shadow-ArUco median 55 px.
- Camera-motion compensation (report row 7) gave no extra recall on this synthetic global shake, added false IDs, and cost 5.7 ms per frame on a PC. It is **out of scope** here. Revisit it with real flight footage.
- With no gate at all, tracked still tops out at 54.4% against 63.8% raw. The 3-of-5 confirmation rule causes the remaining gap, and it is out of scope (approved 2026-11-13).

## Global Constraints

- Settings are constants at the top of `droneload/vision/tracking/tracker.py`: `MIN_GATE_PX = 20.0`, `GATE_SIDES = 0.75`. `MAX_JUMP_PX` is deleted.
- `update()` still returns `(id, cx, cy)` tuples, sorted by ID and rounded to 0.1 px. The CSV columns and values do not change in Tasks 1-2.
- `ARUCO_LABELS`, marker IDs, the default dictionary and the CSV format do not change.
- `CONFIRM_FRAMES`, `WINDOW_FRAMES` and the rule that a far detection counts as a miss for a confirmed track stay as they are.
- Detection-path change: log `python -m testing.benchmark` (expect `found=56.4% unmatched=26.6%`, unchanged) and `--track` before and after. Log the vibration run `python -m testing.vibration_test --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL` before and after (baseline moderate `raw=63.8% tracked=32.6%`).
- Each run of the fdcl vibration test takes about 100 s. Run it only at the steps that ask for it.
- `README.md` and `README.fr.md` change together.
- Branch `fix/tracker-gate`, log `logs/2026-11-16-fix-tracker-gate.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **`--no-track` in `detect.py`:** `found` is never passed through the tracker, so the drawing and CSV loop must not receive 4-tuples. `test_size_filter` and `test_single_frame_needs_no_track` already run this path and must pass.
2. **Same ID detected twice, the far copy much larger:** the gate uses the track's stored side, not the far detection's, so a large false decode cannot widen its own gate. Test `test_gate_uses_track_side` (Task 1).
3. **Tiny marker at `MIN_SIDE_PX = 10` under shake:** the 20 px floor still lets it follow a 15 px per frame move. Test `test_gate_has_pixel_floor` (Task 1).
4. **`benchmark.score` without a tracker:** it must still unpack 4-tuples. `test_score_with_tracker_drops_flicker` covers both paths.
5. **`write_shaken` after `shaken_frames` yields 3-tuples:** `test_write_shaken` covers it and must pass unchanged.

---

### Task 1: Size-scaled gate

**Files:**
- Modify: `droneload/vision/tracking/tracker.py`
- Modify: `droneload/vision/detect.py:166-180` (build 4-tuples, strip the side on the `--no-track` path)
- Modify: `testing/benchmark.py:29-31` (add the side to `found`)
- Modify: `testing/vibration_test.py` (`find_markers` returns 4-tuples, and `is_found` and `shake_run` unpack them)
- Test: `tests/test_tracking.py`
- Docs: `droneload/vision/tracking/README.md` (Results), `droneload/vision/README.md:35,87-94`, `README.md:158`, `README.fr.md:158`, `TODO.md` ("Tracker drops shaken markers"), `logs/DECISIONS.md`

**Interfaces:**
- Produces: `MarkerTracker.update(detections: list[tuple[int, float, float, float]]) -> list[tuple[int, float, float]]`. The input is `(id, cx, cy, side_px)`, where `side_px` is `detect.marker_min_side(corner)`.
- Produces: `vibration_test.find_markers(frame, detector) -> list[tuple[int, float, float, float]]`.
- `_Track` gains `side: float`, set at creation and on every accepted hit.

- [ ] **Step 1: Record the before numbers.** Run `python -m testing.benchmark`, `python -m testing.benchmark --track` and the fdcl vibration run. Note all three in the log. Expected: `56.4/26.6`, `53.2/2.7`, moderate `63.8/32.6`.

- [ ] **Step 2: Write the failing tests.** In `tests/test_tracking.py`, change `run()` so that existing tests keep their 3-tuples and get a default side:

```python
SIDE = 60  # gate max(20, 45) = 45 px, so the existing 30 px/frame and 200 px cases keep their meaning

def run(frames):
    tracker = MarkerTracker()
    return [tracker.update([d if len(d) == 4 else (*d, SIDE) for d in frame]) for frame in frames]

def test_gate_scales_with_marker_side():
    big = run([[(5, 100 * i, 0, 200)] for i in range(6)])      # gate 150 px
    assert all([m[0] for m in o] == [5] for o in big[2:])
    small = run([[(5, 0, 0, 40)]] * 3 + [[(5, 100, 0, 40)]])  # gate 30 px
    assert small[-1] == []

def test_gate_has_pixel_floor():
    out = run([[(5, 15 * i, 0, 10)] for i in range(6)])       # 0.75 x 10 < 20 px floor
    assert all([m[0] for m in o] == [5] for o in out[2:])

def test_gate_uses_track_side():
    out = run([[(3, 100, 100, 40)]] * 3 + [[(3, 300, 100, 400)]])
    assert out[-1] == []
```

- [ ] **Step 3: Run the tests and check they fail.** Run `python -m pytest tests/test_tracking.py -q`. Expected: the three new tests fail (`_Track` takes no side, and the 200 px marker is gated at 40 px). The existing tests may also fail on 4-tuple unpacking.

- [ ] **Step 4: Implement the gate.** In `tracker.py`, replace `MAX_JUMP_PX` with `MIN_GATE_PX = 20.0` ("smallest gate, for small markers") and `GATE_SIDES = 0.75` ("farthest move per frame, in marker sides"). Store `side` on `_Track`. Accept when `math.dist(...) <= max(MIN_GATE_PX, GATE_SIDES * track.side) * track.since_hit`. Pass the side whenever a track is created or replaced. Update the module and `update()` docstrings to say `(id, cx, cy, side_px)`.

- [ ] **Step 5: Update the callers.** Make these changes:
  - `detect.py`: append `(int(marker_id), *center_of(corner), marker_min_side(corner))`. After the tracker block, add an `else` branch that strips the side: `found = [(i, cx, cy) for i, cx, cy, _ in found]`.
  - `benchmark.py`: add `detect.marker_min_side(corner)` to each `found` entry. Without a tracker, unpack with `for marker_id, cx, cy, *_ in found`.
  - `vibration_test.py`: `find_markers` appends `detect.marker_min_side(corner)`. `is_found` and the `raw` set in `shake_run` unpack `marker_id, *_`.

- [ ] **Step 6: Run the checks.** Run `./scripts/check.sh`. Expected: all `[OK]`.

- [ ] **Step 7: Record the after numbers.** Run the three commands from Step 1 again. Expected: benchmark unchanged at `56.4/26.6`. `--track` found ≥ 53.0% and unmatched ≤ 2.7% (prototype: 53.2/2.4). Vibration moderate tracked ≥ 53.5% with false IDs ≤ 0.5 per 100 frames (prototype: 54.1/0.1), and mild tracked ≥ 98%. If any number misses, stop and report. Do not tune constants to fit.

- [ ] **Step 8: Update the docs.** Make these updates:
  - Tracking README Results: the gate sentence and a table row with the after numbers.
  - `vision/README.md`: line 35 and the shake table rows (re-run the Shadow-ArUco shaken numbers with `--source test_footage/shadow-aruco/video_5 --dict DICT_ARUCO_MIP_36h12`), and rewrite line 94, which describes the old 40 px limit.
  - Both READMEs, line 158: the tracked unmatched rate, `2%` if it rounds there.
  - `TODO.md`: tick "Tracker drops shaken markers" with the result. Add one item: the 3-of-5 rule still costs about 10 points under moderate shake (54% against 64%); try ROI re-detection around predictions. Add another: camera-motion compensation showed no gain on synthetic shake, so retest it on flight footage.
  - `logs/DECISIONS.md`: `2026-11-16: The tracker's jump gate is max(20 px, 0.75 × marker side) × frames since last seen, replacing the fixed 40 px.`

- [ ] **Step 9: Commit.**

```bash
git add droneload/vision/tracking/tracker.py droneload/vision/detect.py testing/benchmark.py testing/vibration_test.py tests/test_tracking.py droneload/vision/tracking/README.md droneload/vision/README.md README.md README.fr.md TODO.md logs/DECISIONS.md logs/2026-11-16-fix-tracker-gate.md
git commit -m "Scale the tracker's jump gate with marker size"
```

### Task 2: Position error in the vibration test

The vibration test scores IDs only. This task adds how far each reported position sits from where the marker really is in the shaken frame, so smoothing lag can be measured (report row 2).

**Files:**
- Modify: `testing/vibration_test.py`
- Test: `tests/test_detect.py` (the vibration tests live there)
- Docs: `droneload/vision/README.md` (describe the new columns)

**Interfaces:**
- Consumes: `find_markers` 4-tuples from Task 1.
- Produces: `shake_frame(...) -> tuple[np.ndarray, float, np.ndarray]`, returning the shaken frame, the move in px and the 2×3 affine matrix it applied (rotation, zoom and shift, without blur or wobble). `shaken_frames` yields the same 3-tuple.
- Produces: `map_point(matrix: np.ndarray, x: float, y: float) -> tuple[float, float]`.
- Produces: `position_errors(expected: dict[int, tuple[float, float]], found: dict[int, tuple[float, float]]) -> list[float]`, the distance for each ID present in both.
- `shake_run` returns `(raw, tracked, moves, matrices)`, where `raw` and `tracked` are now `list[dict[int, tuple[float, float]]]`. If an ID appears twice in one frame, keep the first. `shake_rates` uses `.keys()` wherever it used sets.
- Each level's `rates[name]` gains `raw_err_px` and `tracked_err_px`. Each is the mean of `position_errors(expected_i, ...)` over all frames, or `nan` if there are none. `expected_i = {id: map_point(M_i, *clean_raw_i[id]) for id in clean_raw_i if id in real}`.

- [ ] **Step 1: Write the failing tests** in `tests/test_detect.py`:

```python
def test_position_errors_matches_ids():
    assert vibration_test.position_errors({1: (0, 0), 2: (10, 10)}, {1: (3, 4), 3: (0, 0)}) == [5.0]

def test_shake_matrix_maps_marker_centre():
    frames = [vibration_test.make_frame(120)] * 4  # marker centred at (640, 360)
    detector = detect.make_detector()
    for shaken, _, matrix in vibration_test.shaken_frames(frames, vibration_test.SHAKE_LEVELS["mild"]):
        (_, cx, cy, _), = vibration_test.find_markers(shaken, detector)
        assert math.dist((cx, cy), vibration_test.map_point(matrix, 640, 360)) < 2.0

def test_shake_rates_report_position_error():
    frames = [vibration_test.make_frame(240)] * 15
    _, rates = vibration_test.shake_rates(frames, detect.make_detector())
    assert rates["clean"]["raw_err_px"] < 1.0
    assert rates["clean"]["tracked_err_px"] < 1.0
```

In `test_shake_rates_on_footage`, change `shaken, move = ...` to `shaken, move, _ = ...`. Add `import math` if it is missing.

- [ ] **Step 2: Run the tests and check they fail.** Run `python -m pytest tests/test_detect.py -q -k "position or matrix or shake"`. Expected: they fail with `AttributeError` on `position_errors` and `map_point`, or with an unpacking error.

- [ ] **Step 3: Implement** the interfaces above in `vibration_test.py`. `print_shake_table` gains two columns, `raw err` and `tracked err`, in px to one decimal, or `-` for `nan`.

- [ ] **Step 4: Run the checks.** Run `./scripts/check.sh`. Expected: all `[OK]`.

- [ ] **Step 5: Measure smoothing lag.** Run the fdcl vibration test once with `SMOOTHING = 0.6` and once with `SMOOTHING = 1.0`, editing the constant temporarily and reverting it. Log both rows of the `raw err` and `tracked err` columns at clean, mild and moderate. Task 3's decision rests on these numbers. Leave the constant at 0.6 in the commit.

- [ ] **Step 6: Commit.** Describe the columns in `vision/README.md`, then run:

```bash
git add testing/vibration_test.py tests/test_detect.py droneload/vision/README.md logs/2026-11-16-fix-tracker-gate.md
git commit -m "Report position error in the vibration test"
```

### Task 3: Smoothing (needs a decision)

**Stop and ask before starting.** On 2026-11-13 the project lead approved logging smoothed positions (`logs/DECISIONS.md`). Show them the Task 2 Step 5 numbers. Do this task only if they approve `SMOOTHING = 1.0`. Otherwise, record their decision in the log and skip it. The CSV columns do not change either way.

**Files:**
- Modify: `droneload/vision/tracking/tracker.py` (`SMOOTHING = 1.0`, and keep the constant)
- Test: `tests/test_tracking.py`
- Docs: tracking README, `README.md:179`, `README.fr.md:179` ("and its position is smoothed"), `logs/DECISIONS.md`

- [ ] **Step 1: Update the tests.** Replace `test_smooths_position` with `test_reports_detected_position`, asserting `out[-1] == [(1, 10.0, 0.0)]`. In `test_duplicate_id_follows_nearest`, assert `cx == 102`.
- [ ] **Step 2: Run the tests and check they fail.** Run `python -m pytest tests/test_tracking.py -q`. Expected: the two changed tests fail.
- [ ] **Step 3: Set `SMOOTHING = 1.0`.** Then run `./scripts/check.sh`. Expected: all `[OK]`.
- [ ] **Step 4: Update the docs.** Add a DECISIONS line saying that CSV rows hold the detected position of confirmed markers and that it supersedes the smoothed-position wording of 2026-11-13. Update both READMEs and the tracking README together.
- [ ] **Step 5: Commit** the files above by name with the message "Log detected positions instead of smoothed ones".

### Finish

- [ ] Fill in the log's Verification section with every before and after number, and mark anything not run.
- [ ] Push `fix/tracker-gate` to `origin` and open a pull request against `fzizzle/droneload-ESILV-2026-2027` `main`. Say what changed, how it was verified (all numbers) and what remains (the confirmation gap, camera-motion compensation on real footage, nothing tested on hardware).
