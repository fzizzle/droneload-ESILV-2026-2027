# Detection Tuning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Needs the project lead's OK for Task 2:** dropping IDs outside 0-9 changes how marker IDs are handled (`AGENTS.md`, Stop and Ask).

**Goal:** Measure the detector on the contest's own markers, then make only the changes that the measurement supports. Today's baselines come from footage with other dictionaries, filmed in a dark room, so they cannot say whether a change helps at the contest.

**Architecture:** First a test set: the ten contest markers, `DICT_4X4_50`, 20 cm, filmed by hand with a phone so that all ten stay in view. That makes the truth trivial: every frame should hold IDs 0 to 9 once each, and anything else is wrong. A small scoring tool reports found and wrong-ID rates on it. Then four candidate changes are tried one at a time against that set and the existing baselines, and each is kept or dropped on the numbers.

**Tech Stack:** OpenCV, pytest. No new dependency.

**Spec:** `TODO.md` ("Record real `DICT_4X4_50` footage", "`DICT_4X4_50` corrects no bit errors", "Check false positives and missed markers"); `droneload/vision/README.md` ("95% found with the right ID, from 0.5 to 3 m, tilted up to 45°").

## Global Constraints

- **`ARUCO_LABELS`, the default dictionary and the CSV format do not change.**
- Every change in Tasks 2 to 5 is a detection change: run `python -m testing.benchmark`, `python -m testing.benchmark --track` and the vibration baseline before and after, and log all of them beside the new set's scores. Baselines: `found=57.6% unmatched=4.1%`, `found=54.8% unmatched=0.8%`, moderate `raw=65.9% tracked=57.2%`.
- One change per task and per commit, so each can be reverted alone.
- **Keep a change only if** the new set's found rate rises or its wrong-ID rate falls, and neither gets worse by more than 0.5 points, and the old baselines do not get worse by more than 1 point. Otherwise revert it and record the numbers in `TODO.md`.
- Footage is never committed. It goes in `test_footage/contest/`, with a line in the README's Test Footage section saying how to make it.
- PC timings do not transfer to the companion computer. Record them, marked as PC figures.
- Branch `test/contest-footage` for Task 1, then one `fix/...` branch per kept change, each with its own log.

## Review Focus

1. **A frame where a marker is truly out of view:** the scoring assumes all ten are visible. Clips are filmed to keep them in view, and the tool reports frames with fewer than 5 markers found separately, so a bad clip shows up rather than hiding as a low score. Test `test_sparse_frames_are_reported` (Task 1).
2. **The same ID found twice in a frame:** counts as one found and one wrong. Test `test_duplicate_id_counts_as_wrong` (Task 1).
3. **A wrong ID inside 0-9:** the ID filter cannot remove it, so the tool reports wrong IDs in and out of the range separately. Test `test_wrong_ids_are_split_by_range` (Task 1).
4. **Error correction turned up without the ID filter:** it raises false positives across all 50 IDs. Task 3 depends on Task 2 for that reason and must not be merged without it.
5. **Corner refinement and the tracker's gate:** refined corners move by under a pixel, so the gate and the 15 px benchmark match must be unaffected. Task 5 checks the tracked scores as well as the raw ones.

---

### Task 1: Contest footage and its score

**Files:**
- Create: `testing/contest_score.py`
- Test: `tests/test_contest_score.py`
- Docs: `README.md` and `README.fr.md` (Test Footage, Project Structure), `droneload/vision/README.md` (Measured So Far), `AGENTS.md` (Verification: add the new command and its baseline), `logs/DECISIONS.md`, `TODO.md`

**Interfaces:**
- Produces: `python -m testing.contest_score [--footage test_footage/contest] [--track]` prints one line per clip and a total: `clip=NAME frames=N found=X% wrong_in=Y wrong_out=Z sparse=S ms=T`. `found` is the share of the expected 10 × N markers found with the right ID; `wrong_in` and `wrong_out` are wrong or duplicate detections per 100 frames, with IDs inside and outside 0-9; `sparse` counts frames with fewer than 5 found; `ms` is the mean detection time. `score_frames(frames, detector, tracker=None, expected=range(10)) -> dict`.

- [ ] **Step 1: Print and film.** Print markers 0 to 9 from `DICT_4X4_50` at exactly 20 cm (measure them) and lay them on the floor in a 2 × 5 grid with 30 cm gaps. With a phone at 1080p and 30 fps, film six 20-second clips, keeping all ten in view: `still-1m`, `still-2m`, `still-3m` (held as steady as possible), `tilt-45` (circling at 2 m, tilted up to 45°), `shake` (at 2 m, shaken as a vibrating mount would), and `dim` (at 2 m with the lights down). Note the phone and the lighting in the log.
- [ ] **Step 2: Write the failing tests,** on rendered frames from `testing.sim_camera`: `test_all_found_scores_100`, `test_missing_marker_lowers_found`, `test_duplicate_id_counts_as_wrong`, `test_wrong_ids_are_split_by_range`, `test_sparse_frames_are_reported`.
- [ ] **Step 3: Run them and check they fail.**
- [ ] **Step 4: Implement.**
- [ ] **Step 5: Run it on the six clips, with and without `--track`.** These numbers are the new baseline. Put them in the log, the `vision` README, `logs/DECISIONS.md` and `AGENTS.md`.
- [ ] **Step 6: Run `./scripts/check.sh`, update the docs and commit.** Message "Add a detection score on the contest's own markers".

### Task 2: Report only contest IDs

**Files:**
- Modify: `droneload/vision/detect.py`
- Test: `tests/test_detect.py`

**Interfaces:**
- Produces: `ALLOWED_IDS = frozenset(ARUCO_LABELS)` at the top of `detect.py`. Detections with other IDs are dropped before tracking when the dictionary is the default; with `--dict` set to another dictionary, nothing is dropped, so the old benchmarks still run.

- [ ] **Step 1: Before numbers.** Step 2: failing tests `test_other_ids_are_dropped` (a frame with markers 3 and 17 reports only 3) and `test_other_dictionaries_are_not_filtered`. Step 3: check they fail. Step 4: implement. Step 5: after numbers; expected `wrong_out=0` and unchanged old baselines. Step 6: apply the keep rule, update `droneload/vision/README.md`, and commit. Message "Report only the contest's marker IDs".

### Task 3: One-bit error correction

`DICT_4X4_50` with OpenCV's default `errorCorrectionRate = 0.6` corrects no bits, so one cell flipped by blur loses the marker (`TODO.md`).

**Files:**
- Modify: `droneload/vision/detect.py` (`make_detector`)
- Test: `tests/test_detect.py`

- [ ] **Step 1: Before numbers.** Step 2: failing test `test_one_flipped_cell_is_still_read` (a rendered marker 0 with one inner cell inverted is reported as 0). Step 3: check it fails. Step 4: set `params.errorCorrectionRate = 1.0`. Step 5: after numbers; watch `wrong_in` on the `shake` and `dim` clips above all. Step 6: apply the keep rule and commit or revert. Message "Correct one flipped bit in DICT_4X4_50 markers".

### Task 4: Preprocessing and threshold passes

Two settings may cost time without helping: CLAHE before a detector that already thresholds adaptively, and six threshold window sizes (3 to 53 in steps of 10).

**Files:**
- Modify: `droneload/vision/detect.py`
- Test: `tests/test_detect.py` only if behaviour changes

- [ ] **Step 1: Before numbers, with `ms`.** Step 2: score four variants without committing any: CLAHE off; windows 3 to 23 in steps of 10; both; neither (today's). Put the table in the log. Step 3: adopt the variant with the lowest `ms` among those that pass the keep rule; if none passes, change nothing. Step 4: after numbers. Step 5: commit, or record the table in `TODO.md` and stop. Message names the setting changed.

### Task 5: Sub-pixel corners

Corner refinement does not find more markers; it places their corners better, which matters for distances from `solvePnP`.

**Files:**
- Modify: `droneload/vision/detect.py` (`make_detector`)
- Test: `tests/test_detect.py`
- Docs: `droneload/vision/README.md` (Position Accuracy table)

- [ ] **Step 1: Before numbers,** plus the Position Accuracy table's errors at 1, 2, 3 and 5 m, regenerated with today's code. Step 2: failing test `test_refined_corners_improve_distance` (the mean distance error at 3 m over 40 rendered placements is at least 30% lower than without refinement). Step 3: check it fails. Step 4: set `params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX`. Step 5: after numbers, the accuracy table and `ms`. Step 6: keep it only if the distance error improves, the keep rule holds and `ms` rises by under 30%. Update the table and commit, or revert. Message "Refine marker corners to sub-pixel accuracy".

## Done When

- [ ] The contest clips exist, and their baseline is in `AGENTS.md` beside the old ones.
- [ ] Each of Tasks 2 to 5 is either merged with its numbers or recorded in `TODO.md` as tried and dropped, with its numbers.
- [ ] `./scripts/check.sh` passes for each branch, and each pull request is open.

## After This Plan

- Refilm the six clips with the chosen camera when it arrives, and from the drone in a hover (Stage 7 of `docs/plans/2026-11-18-kit-bring-up.md`). Those replace the phone clips as the baseline.
- Measure `ms` on the companion computer. Only if it misses 30 frames per second: detect on a half-size image first, or search near the last position; both are untested ideas, not plans.
