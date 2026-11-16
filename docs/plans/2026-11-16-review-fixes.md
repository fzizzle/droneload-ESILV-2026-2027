# Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bugs the 2026-11-16 performance review found in the detection loop and the benchmark, and adopt the one detector setting the review measured as better.

**Architecture:** Four branches, one purpose each, merged in order. The benchmark is fixed first, because every later detection change is judged against its baseline. The loop then gets its timing fixed (no sleep, video time for files, correct recording speed), then its failure handling (dead camera, bad `--dict`). The detector setting changes last, measured against the corrected baseline.

**Tech Stack:** Python standard library, OpenCV, numpy, pytest. No new dependency.

**Spec:** "Review Findings" below. Decisions marked *approved* were made by the project lead on 2026-11-16.

## Review Findings (2026-11-16, before planning)

Measured with throwaway scripts on a PC, OpenCV limited to 4 threads. Nothing was committed.

| # | Finding | Evidence |
|---|---|---|
| 1 | `benchmark.py` does not apply `MIN_SIDE_PX`, so it scores detections the app discards | With the filter: `found=56.4% unmatched=10.9%`, not `unmatched=26.6%`. With `--track`: `found=53.3% unmatched=1.4%` |
| 2 | The loop sleeps 10 ms per frame (`detect.py:237`); detection takes about 4 ms | Generated test video: 72 fps with the sleep, 285 fps without |
| 3 | CSV timestamps and the 1 s cooldown use the wall clock for video files | The 5 s test video logs 9 rows with the sleep and 3 without; video time gives 15 |
| 4 | `--record` always writes at 30 fps | The recording plays at the wrong speed unless the loop runs at exactly 30 fps |
| 5 | A dead live camera prints a warning 20 times a second forever | Read from `detect.py:149-151` |
| 6 | A mistyped `--dict` raises after the camera is opened, so the camera is not released | Read from `detect.py:120-125` |
| 7 | `polygonalApproxAccuracyRate = 0.05` is worse than OpenCV's default of 0.03 | Table below |

| | 0.05 (now) | 0.03 |
|---|---|---|
| Shadow-ArUco found / unmatched, with the size filter | 56.4% / 10.9% | 57.6% / 4.1% |
| Same, with tracking | 53.3% / 1.4% | 54.8% / 0.8% |
| fdcl-gwu moderate shake, raw / tracked | 63.8% / 54.1% | 65.9% / 57.2% |
| fdcl-gwu severe shake, raw | 3.9% | 2.4% |
| Detection time per frame | 4.5 ms | 4.0 ms |

Decisions:

- *Approved:* for a video file, `timestamp_ms` is the time the run started plus the frame's position in the video, and the cooldown follows it. Live cameras keep the wall clock.
- *Approved:* after 2 s without a frame, a live camera is released and reopened, and again every 2 s, with one warning per attempt.
- *Approved:* the `flight` fix (`COMMAND_ACK`) is not in this plan. It is in `TODO.md`.
- CLAHE and the six threshold windows stay. Removing either costs 6 to 9 points of `found`.
- Findings that need hardware (Picamera2 colour order, CSI grey plane, USB MJPG) are in `TODO.md`, not here.

## Global Constraints

- The CSV columns stay `timestamp_ms,id,label,cx,cy`. `ARUCO_LABELS`, marker IDs and the default dictionary do not change.
- No new dependency.
- Settings are constants at the top of `droneload/vision/detect.py`.
- Tests go in `tests/`. Tests that run `detect.main()` call `monkeypatch.chdir(tmp_path)` first, because it writes `detections.csv` and `aruco_debug.jpg` to the current folder.
- `README.md` and `README.fr.md` change together.
- Run `source .venv/bin/activate` before `./scripts/check.sh`.
- Each fdcl-gwu vibration run takes about 100 s. Run it only where a step asks for it.
- Camera behaviour is tested here with fake cameras only. Say "unverified on hardware" in the log and the pull request.
- Before any `gh pr` command, run `gh repo set-default --view`. If it does not print `fzizzle/droneload-ESILV-2026-2027`, pass `--repo fzizzle/droneload-ESILV-2026-2027`. Never push to `upstream`.

## Branches

| Branch | Tasks | Log |
|---|---|---|
| `fix/benchmark-size-filter` | 1 | `logs/2026-11-16-fix-benchmark-size-filter.md` |
| `fix/detect-loop-timing` | 2, 3, 4 | `logs/2026-11-16-fix-detect-loop-timing.md` |
| `fix/camera-failures` | 5, 6 | `logs/2026-11-16-fix-camera-failures.md` |
| `fix/polygon-accuracy` | 7 | `logs/2026-11-16-fix-polygon-accuracy.md` |

Use the day's date in the log name if the work starts later. The last three branches all edit `detect.py`, so start each from `main` after the previous pull request is merged. If it is not merged yet, branch from the previous branch and say so in the pull request.

**To start a branch:** create it, then create its log from `logs/TEMPLATE.md` (20 lines at most).

**To finish a branch:** run `./scripts/check.sh` (all four lines `[OK]`), update the log, tick the matching `TODO.md` items if any, commit, push to `origin`, and open a pull request that says what changed, how it was verified and what remains.

## Review Focus

Conditions the findings imply but do not test, most likely first. Each has a test in the task named.

1. A video file or image sequence that reports no frame rate, or a camera object without `fps`: rows are spaced as at 30 fps, with no division by zero. (Task 3)
2. A camera that never comes back: the loop retries every 2 s with one warning per attempt, and Ctrl+C still exits cleanly. (Task 5)
3. A live loop faster than 30 fps while recording: frames are skipped, not written early. (Task 4)
4. A file with a non-integer frame rate, such as 29.97 (fdcl-gwu reports 30.03): the recording keeps it. (Task 4)
5. A dictionary name in the wrong case, such as `dict_4x4_50`: a clear error before the camera opens. (Task 6)

---

## Branch `fix/benchmark-size-filter`

### Task 1: The benchmark applies the app's size filter

**Files:**
- Modify: `testing/benchmark.py:28-31`
- Test: `tests/test_benchmark.py`
- Modify: `AGENTS.md:68`, `droneload/vision/README.md:34-35`, `logs/DECISIONS.md`, `TODO.md` ("Check false positives and missed markers on real footage")

**Interfaces:**
- Consumes: `vibration_test.find_markers(frame, detector)`, which returns `(id, cx, cy, side_px)` per marker, already "filtered as the detection loop does".
- Produces: `benchmark.score(paths, detector, tracker=None)`, unchanged signature and return value.

- [ ] **Step 1: Record the old baseline**

Run: `python -m testing.benchmark` and `python -m testing.benchmark --track`
Expected: `found=56.4% unmatched=26.6%` and `found=53.2% unmatched=2.4%`. Put both in the log.

- [ ] **Step 2: Write the failing test** in `tests/test_benchmark.py`

```python
def test_score_applies_size_filter(tmp_path, monkeypatch):
    paths = write_frames(tmp_path)
    monkeypatch.setattr(detect, "MIN_SIDE_PX", 200)   # larger than the 150 px markers

    assert benchmark.score(paths, detect.make_detector("DICT_4X4_50")) == (0, 0, 6)
```

- [ ] **Step 3: Run it to see it fail**

Run: `python -m pytest tests/test_benchmark.py::test_score_applies_size_filter -q`
Expected: FAIL, `(6, 0, 6) != (0, 0, 6)`

- [ ] **Step 4: Use the shared detection helper in `score()`**

Replace the grey conversion, the `detectMarkers` call and the `found` comprehension with `found = vibration_test.find_markers(cv2.imread(path), detector)`. Import it with `from testing import vibration_test`. Remove imports this leaves unused.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_benchmark.py -q`
Expected: 2 passed

- [ ] **Step 6: Record the new baseline and update the documents**

Run both benchmark commands again. Expected: about `found=56.4% unmatched=10.9%` and `found=53.3% unmatched=1.4%`. Use the measured numbers below, not these.

- `AGENTS.md:68`: replace the baseline.
- `droneload/vision/README.md:34-35`: replace both rows' results.
- `TODO.md`, "Check false positives…": replace "27% of its detections did not match" and the tracking numbers.
- `logs/DECISIONS.md`: add `- <date>: The benchmark applies MIN_SIDE_PX as the app does. The baseline is now found=<x>% unmatched=<y>%, superseding unmatched=26.6%.`

- [ ] **Step 7: Commit**

```bash
git add testing/benchmark.py tests/test_benchmark.py AGENTS.md droneload/vision/README.md TODO.md logs/DECISIONS.md logs/2026-11-16-fix-benchmark-size-filter.md
git commit -m "Apply the size filter in the benchmark"
```

Then finish the branch.

---

## Branch `fix/detect-loop-timing`

### Task 2: Remove the per-frame sleep

**Files:**
- Modify: `droneload/vision/detect.py:237`
- Test: `tests/test_detect.py`

- [ ] **Step 1: Record the loop speed before**

In a scratch folder outside the repository, run `python -m testing.make_test_video`, then `time python -m droneload.vision --source test_markers.mp4` with `PYTHONPATH` set to the repository. Put the wall time for the 150 frames in the log.

- [ ] **Step 2: Write the failing test**

```python
def test_loop_does_not_sleep_between_frames(tmp_path, monkeypatch):
    slept = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect.time, "sleep", slept.append)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([one_marker_frame()] * 3))
    monkeypatch.setattr(sys, "argv", ["detect"])
    detect.main()

    assert slept == []
```

- [ ] **Step 3: Run it to see it fail**

Run: `python -m pytest tests/test_detect.py::test_loop_does_not_sleep_between_frames -q`
Expected: FAIL, `[0.01, 0.01, 0.01] != []`

- [ ] **Step 4: Delete `time.sleep(0.01)` at the end of the loop.** Keep the `time.sleep(0.05)` after a failed read.

- [ ] **Step 5: Run the test, then repeat Step 1** and log the new wall time (the review measured 2.1 s → 0.5 s).

- [ ] **Step 6: Commit**

```bash
git add droneload/vision/detect.py tests/test_detect.py
git commit -m "Remove the 10 ms sleep from the detection loop"
```

### Task 3: Video files keep their own time in the CSV

**Files:**
- Modify: `droneload/vision/camera_opencv.py:18-27`, `droneload/vision/detect.py` (helpers and the loop)
- Test: `tests/test_detect.py`
- Modify: `README.md:222`, `README.fr.md:222`, `logs/DECISIONS.md`

**Interfaces:**
- Produces: `detect.source_fps(camera) -> float | None`. Task 4 uses it.
- Produces in tests: `write_video(path, frames, fps)` and `logged_rows()`. Task 4 uses `write_video`.

- [ ] **Step 1: Write the failing tests**

```python
def write_video(path, frames, fps):
    height, width = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for frame in frames:
        writer.write(frame)
    writer.release()

def logged_rows():
    with open(detect.DETECTION_LOG, newline="") as f:
        return [(int(row["timestamp_ms"]), int(row["id"])) for row in csv.DictReader(f)]

def test_source_fps(tmp_path):
    write_video(tmp_path / "slow.mp4", [one_marker_frame()] * 3, 10)
    camera = OpenCVCamera(str(tmp_path / "slow.mp4"))
    assert camera.open()
    assert detect.source_fps(camera) == pytest.approx(10)
    camera.release()

    live = FakeCamera([])
    live.finite = False
    assert detect.source_fps(live) is None

def test_source_fps_falls_back():
    camera = FakeCamera([])                       # finite, with no fps
    assert detect.source_fps(camera) == detect.RECORD_FPS
    camera.fps = 0                                # a file that reports no frame rate
    assert detect.source_fps(camera) == detect.RECORD_FPS

def test_video_file_rows_follow_video_time(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    make_test_video.main()                        # 150 frames at 30 fps: 5 s of video
    monkeypatch.setattr(sys, "argv", ["detect", "--source", make_test_video.OUTPUT])
    before = detect.now_ms()
    detect.main()

    rows = logged_rows()
    for marker_id in make_test_video.MARKER_IDS:
        times = [ts for ts, logged_id in rows if logged_id == marker_id]
        assert len(times) == 5                    # one row per second of video, on any computer
        assert all(1000 <= b - a < 1100 for a, b in zip(times, times[1:]))
        assert before <= times[0] < before + 60_000
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_detect.py -q -k "source_fps or video_time"`
Expected: FAIL, `detect` has no `source_fps`

- [ ] **Step 3: Make `OpenCVCamera.open()` learn a file's frame rate**

For a finite source, after it opens: `self.fps = self.cap.get(cv2.CAP_PROP_FPS) or self.fps`. An image sequence reports 25.

- [ ] **Step 4: Add `source_fps(camera)` to `detect.py`**

Return `None` unless `camera.finite` is true. Otherwise return `camera.fps`, or `RECORD_FPS` when the attribute is missing or 0. Extend the `RECORD_FPS` comment: it is also the rate assumed for a file that reports none.

- [ ] **Step 5: Use it for `ts` in the loop**

Before the loop, read `file_fps = source_fps(camera)` and `start_ms = now_ms()`, and count frames read from 0. Then:

```python
ts = now_ms() if file_fps is None else start_ms + round(1000 * frame_index / file_fps)
```

`now`, which paces the terminal log and the debug image, stays on the wall clock.

- [ ] **Step 6: Run the tests**

Run: `python -m pytest tests/test_detect.py -q`
Expected: all pass

- [ ] **Step 7: Update the documents**

- `README.md:222`: `5. Logs each marker ID at most once per second (`WRITE_COOLDOWN_MS`), which keeps the CSV small. For a live camera, this limit and `timestamp_ms` use real time. For a video file, they use the time the run started plus the frame's position in the video, so the same file gives equally spaced rows on any computer.`
- `README.fr.md:222`: `5. Enregistrement de chaque ID au plus une fois par seconde (`WRITE_COOLDOWN_MS`), pour limiter la taille du CSV. Avec une caméra, cette limite et `timestamp_ms` suivent le temps réel. Avec un fichier vidéo, ils suivent l'heure de lancement plus la position de l'image dans la vidéo : un même fichier produit donc des lignes espacées de la même façon sur tout ordinateur.`
- `logs/DECISIONS.md`: `- 2026-11-16: For a video file, CSV timestamps and the cooldown follow the run's start time plus the frame's position in the video; live cameras keep real time. The columns are unchanged. Approved by the project lead.`

- [ ] **Step 8: Commit**

```bash
git add droneload/vision/camera_opencv.py droneload/vision/detect.py tests/test_detect.py README.md README.fr.md logs/DECISIONS.md
git commit -m "Time CSV rows by video position for video files"
```

### Task 4: Recordings play at the right speed

**Files:**
- Modify: `droneload/vision/detect.py` (helper and the `--record` block)
- Test: `tests/test_detect.py`
- Modify: `README.md:182`, `README.fr.md:182`

**Interfaces:**
- Consumes: `detect.source_fps(camera)` and `write_video(path, frames, fps)` from Task 3.
- Produces: `detect.frames_due(elapsed_s: float, written: int, fps: float = RECORD_FPS) -> int`, the number of copies of the current frame to write so the recording keeps real time. It returns `max(0, int(elapsed_s * fps) + 1 - written)`.

- [ ] **Step 1: Write the failing tests**

```python
class LiveCamera(FakeCamera):
    """A live source that ends with Ctrl+C when its frames run out."""
    finite = False

    def read(self):
        if not self.frames:
            raise KeyboardInterrupt
        return True, self.frames.pop()

def recorded(path):
    video = cv2.VideoCapture(path)
    return video.get(cv2.CAP_PROP_FPS), int(video.get(cv2.CAP_PROP_FRAME_COUNT))

def test_frames_due_keeps_real_time():
    assert detect.frames_due(0.0, 0) == 1     # the first frame is written at once
    assert detect.frames_due(0.01, 1) == 0    # loop faster than 30 fps: skip the frame
    assert detect.frames_due(0.25, 2) == 6    # loop slower: repeat the frame

@pytest.mark.parametrize("fps", [10, 29.97])
def test_record_keeps_the_file_frame_rate(tmp_path, monkeypatch, fps):
    monkeypatch.chdir(tmp_path)
    write_video("in.mp4", [one_marker_frame()] * 12, fps)
    monkeypatch.setattr(sys, "argv", ["detect", "--source", "in.mp4", "--record", "out.mp4"])
    detect.main()

    out_fps, count = recorded("out.mp4")
    assert out_fps == pytest.approx(fps, abs=0.05)
    assert count == 12

def test_live_recording_writes_the_frames_due(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: LiveCamera([one_marker_frame()] * 3))
    monkeypatch.setattr(detect, "frames_due", lambda elapsed_s, written: 2)
    monkeypatch.setattr(sys, "argv", ["detect", "--record", "out.mp4"])
    detect.main()

    assert recorded("out.mp4") == (pytest.approx(detect.RECORD_FPS), 6)
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_detect.py -q -k "frames_due or record"`
Expected: FAIL, `detect` has no `frames_due`

- [ ] **Step 3: Add `frames_due` to `detect.py`** with the signature and formula in Interfaces.

- [ ] **Step 4: Change the `--record` block**

Open the writer at `file_fps or RECORD_FPS`. For a file (`file_fps` is not `None`), write each frame once. For a live source, note `time.perf_counter()` when the writer opens, and write the frame `frames_due(elapsed, written)` times, counting what is written.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_detect.py -q`
Expected: all pass, including the existing `test_record_writes_annotated_video` (150 frames)

- [ ] **Step 6: Update both READMEs at line 182**, after "`--record out.mp4` saves the same video."

- English: `A recording of a video file keeps the file's frame rate. A recording of a live camera is written at 30 fps in real time, so frames are repeated or skipped when the loop runs slower or faster.`
- French: `L'enregistrement d'un fichier vidéo conserve sa fréquence d'images. Celui d'une caméra est écrit à 30 images par seconde en temps réel : des images sont répétées ou sautées si la boucle tourne plus lentement ou plus vite.`

- [ ] **Step 7: Commit**

```bash
git add droneload/vision/detect.py tests/test_detect.py README.md README.fr.md
git commit -m "Record at the source's frame rate, in real time for live cameras"
```

Then finish the branch.

---

## Branch `fix/camera-failures`

### Task 5: Reopen a camera that stops sending frames

**Files:**
- Modify: `droneload/vision/detect.py:141-151` and the constants
- Test: `tests/test_detect.py`
- Modify: `README.md`, `README.fr.md` (after the sources table, near line 178)

**Interfaces:**
- Produces: constant `REOPEN_AFTER_SEC = 2.0` in `detect.py`.

- [ ] **Step 1: Write the failing tests**

```python
class FlakyCamera:
    """Live camera that sends no frames until it has been opened more than dead_opens times."""
    finite = False

    def __init__(self, frames, dead_opens, max_reads=20):
        self.frames, self.dead_opens, self.reads_left = frames, dead_opens, max_reads
        self.opens = self.releases = 0

    def open(self):
        self.opens += 1
        return self.opens == 1 or self.opens > self.dead_opens

    def read(self):
        self.reads_left -= 1
        alive = self.opens > self.dead_opens
        if self.reads_left < 0 or (alive and not self.frames):
            raise KeyboardInterrupt               # stands in for Ctrl+C
        return (True, self.frames.pop()) if alive else (False, None)

    def release(self):
        self.releases += 1

def run_flaky(tmp_path, monkeypatch, camera):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "REOPEN_AFTER_SEC", 0)
    monkeypatch.setattr(detect.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(detect, "make_camera", lambda source: camera)
    monkeypatch.setattr(sys, "argv", ["detect", "--no-track"])
    detect.main()

def test_dead_camera_is_reopened(tmp_path, monkeypatch, capsys):
    camera = FlakyCamera([one_marker_frame()], dead_opens=1)
    run_flaky(tmp_path, monkeypatch, camera)

    assert camera.opens == 2
    assert logged_ids() == {0}
    assert capsys.readouterr().out.count("[WARNING]") == 2   # frames lost, then one reopen

def test_camera_that_never_returns_keeps_retrying(tmp_path, monkeypatch, capsys):
    camera = FlakyCamera([], dead_opens=99, max_reads=6)
    run_flaky(tmp_path, monkeypatch, camera)      # ends on Ctrl+C without raising

    assert camera.opens == 6                      # the first open, then one per failed read after the first
    assert camera.releases == 6                   # each reopen releases first; so does the exit
    assert logged_ids() == set()
    assert capsys.readouterr().out.count("[WARNING]") == 6   # one per attempt, not one per read
```

- [ ] **Step 2: Run them to see them fail**

Run: `python -m pytest tests/test_detect.py -q -k "dead_camera or never_returns"`
Expected: FAIL, `detect` has no `REOPEN_AFTER_SEC`

- [ ] **Step 3: Replace the failed-read branch for live sources**

Keep the finite-source branch as it is. For a live source, remember when reads began to fail, on `time.monotonic()`:

- first failed read: print `[WARNING] No frame from the camera. Retrying.` once, and do nothing else
- on a later failed read, once failures have lasted `REOPEN_AFTER_SEC`: print `[WARNING] Reopening the camera.`, call `camera.release()` then `camera.open()`, and restart the count from now, whether or not the open succeeded
- a good frame clears the failure state

Keep `time.sleep(0.05)` between failed reads.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_detect.py -q`
Expected: all pass

- [ ] **Step 5: Add one sentence to both READMEs** after the sources table

- English: `If a live camera stops sending frames, the program reopens it every 2 s until frames return.`
- French: `Si une caméra cesse d'envoyer des images, le programme la rouvre toutes les 2 s jusqu'au retour des images.`

Add to `TODO.md` under Bugs: `- [ ] **Check camera reopening on hardware.** The loop reopens a camera after 2 s without frames; this is tested with a fake camera only.`

- [ ] **Step 6: Commit**

```bash
git add droneload/vision/detect.py tests/test_detect.py README.md README.fr.md TODO.md
git commit -m "Reopen a live camera that stops sending frames"
```

### Task 6: Reject an unknown `--dict` before the camera opens

**Files:**
- Modify: `droneload/vision/detect.py` (constants and the `--dict` argument)
- Test: `tests/test_detect.py`

**Interfaces:**
- Produces: `detect.ARUCO_DICTS`, the sorted names in `cv2.aruco` that start with `DICT_`.

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.parametrize("name", ["DICT_NOPE", "dict_4x4_50"])
def test_unknown_dict_rejected_before_camera_opens(monkeypatch, name):
    opened = []
    monkeypatch.setattr(detect, "make_camera", opened.append)
    monkeypatch.setattr(sys, "argv", ["detect", "--dict", name])
    with pytest.raises(SystemExit) as error:
        detect.main()

    assert error.value.code == 2
    assert opened == []
```

- [ ] **Step 2: Run it to see it fail**

Run: `python -m pytest tests/test_detect.py -q -k unknown_dict`
Expected: FAIL, `opened` is `['0']` and an `AttributeError` is raised instead of `SystemExit`

- [ ] **Step 3: Add `ARUCO_DICTS` next to `ARUCO_DICT`, and pass `choices=ARUCO_DICTS, metavar="DICTIONARY"` to the `--dict` argument.** `argparse` then exits with code 2 and names the valid choices, before `make_camera` runs.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_detect.py -q`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add droneload/vision/detect.py tests/test_detect.py
git commit -m "Reject an unknown dictionary before opening the camera"
```

Then finish the branch, and tick nothing in `TODO.md` that still needs hardware.

---

## Branch `fix/polygon-accuracy`

### Task 7: Use OpenCV's default polygon accuracy

Start this branch only after `fix/benchmark-size-filter` is merged, so the "before" numbers use the corrected benchmark.

**Files:**
- Modify: `droneload/vision/detect.py:58`, `analysis/smoothing/study.py:27`
- Test: `tests/test_detect.py`
- Modify: `AGENTS.md:68-70`, `droneload/vision/README.md:34-35`, `logs/DECISIONS.md`, `TODO.md`

- [ ] **Step 1: Record all three results before the change**

```bash
python -m testing.benchmark
python -m testing.benchmark --track
python -m testing.vibration_test --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL
```

Expected: the baselines in `AGENTS.md` (moderate `raw=63.8% tracked=54.1%`, tracked err 1.7 px). Summarise them in the log.

- [ ] **Step 2: Write the failing test**

```python
def test_detector_uses_default_polygon_accuracy():
    params = detect.make_detector().getDetectorParameters()
    assert params.polygonalApproxAccuracyRate == pytest.approx(0.03)
```

- [ ] **Step 3: Run it to see it fail**

Run: `python -m pytest tests/test_detect.py -q -k polygon`
Expected: FAIL, `0.05 != 0.03`

- [ ] **Step 4: Delete `params.polygonalApproxAccuracyRate = 0.05` from `make_detector()`.** Keep `minMarkerPerimeterRate` and its comment.

- [ ] **Step 5: Bump `CACHE_VERSION` to 3 in `analysis/smoothing/study.py`,** so detections cached with the old setting are not reused.

- [ ] **Step 6: Run the checks and repeat Step 1**

Run: `./scripts/check.sh`, then the three commands.
Expected, from the review: benchmark about `found=57.6% unmatched=4.1%`; with `--track` about `54.8% / 0.8%`; moderate shake about `raw=65.9% tracked=57.2%`; severe raw falls from 3.9% to about 2.4%.

**Stop and report instead of committing** if `found` or moderate `tracked` is lower than before, or `unmatched` is higher. If a test fails because it pinned behaviour of the 0.05 setting, report that too.

- [ ] **Step 7: Update the documents with the measured numbers**

- `AGENTS.md`: both baselines (benchmark and moderate shake).
- `droneload/vision/README.md:34-35`: both rows.
- `TODO.md`: the numbers in "Check false positives…", and any other entry that quotes a baseline this changes.
- `logs/DECISIONS.md`: `- <date>: polygonalApproxAccuracyRate returns to OpenCV's default 0.03 (was 0.05). Baselines are now found=<x>% unmatched=<y>%, and moderate shake raw=<a>% tracked=<b>%.`

- [ ] **Step 8: Commit**

```bash
git add droneload/vision/detect.py analysis/smoothing/study.py tests/test_detect.py AGENTS.md droneload/vision/README.md TODO.md logs/DECISIONS.md logs/2026-11-16-fix-polygon-accuracy.md
git commit -m "Use OpenCV's default polygon accuracy"
```

Then finish the branch. In the pull request, say that neither footage uses `DICT_4X4_50` and that severe shake got slightly worse.
