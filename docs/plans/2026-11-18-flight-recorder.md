# Flight Recorder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Save everything a flight produced, so it can be replayed on a PC afterwards. Cage time is scarce; each flight should answer questions for weeks, not once.

**Architecture:** Each mission run writes one folder: the raw frames of each camera as a video with a timestamp per frame, the MAVLink traffic as a `.tlog` file that ground stations open, and the mission's events as one JSON object per line. All three carry the same clock. Raw frames, not annotated ones, so the detector can be rerun on them after it changes.

**Tech Stack:** OpenCV `VideoWriter`, `pymavlink`'s timestamped log file, the standard library's `json`. No new dependency.

**Spec:** `docs/plans/2026-11-18-roadmap.md`; `droneload/mission/README.md` ("Each state change is logged").

## Global Constraints

- Needs these plans merged: `vision-api`, `flight-velocity`, `mission-runner`.
- Folder: `flights/YYYYMMDD-HHMMSS-<plan>/`, holding `down.mp4`, `down.csv`, `forward.mp4`, `forward.csv`, `telemetry.tlog`, `events.jsonl` and `meta.json`. `flights/` is added to `.gitignore`: footage is never committed.
- Recording must never slow or stop a flight. Frames are written by a thread from a queue of at most `QUEUE_FRAMES = 30`; when it is full, frames are dropped and counted.
- Every record carries `t`, seconds since the run started, from the runner's clock.
- Settings are constants at the top of `droneload/mission/recorder.py`: `RECORD_FPS = 15`, `RECORD_CODEC = "mp4v"`, `QUEUE_FRAMES = 30`, `MIN_FREE_MB = 500`.
- The `.tlog` is written by `flight`, because only `flight` holds the MAVLink connection. That is flight controller code and needs the project lead's OK; it only writes to disk.
- **Unverified until measured on the companion computer:** that it can encode two 720p streams at 15 fps beside detection. Task 4 measures it on a PC and leaves the board figure open.
- Branch `feature/flight-recorder`, log `logs/YYYY-MM-DD-feature-flight-recorder.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Disk full or nearly full:** below `MIN_FREE_MB` at start, recording is off with one warning and the mission runs. A write error in flight turns recording off the same way. Test `test_low_disk_turns_recording_off` and `test_write_error_is_survived` (Task 1).
2. **Crash or power cut in mid-flight:** the events file is flushed per line and the timestamp file per frame, so what was written stays readable. Test `test_files_are_readable_after_a_kill` (Task 2).
3. **A frame size that changes after a camera reopen:** the writer starts a second file (`down-2.mp4`) rather than writing frames `VideoWriter` drops silently (`TODO.md`, camera reopening). Test `test_new_frame_size_starts_a_new_file` (Task 1).
4. **Two runs in the same second:** the second folder gets a `-2` suffix. Test `test_folder_names_do_not_collide` (Task 2).
5. **Replay at the wrong speed:** the timestamp file, not the video's nominal frame rate, gives each frame's time. Test `test_replay_uses_recorded_times` (Task 3).

---

### Task 1: Frame recorder

**Files:**
- Create: `droneload/vision/recording.py`
- Test: `tests/test_recording.py`

**Interfaces:**
- Produces:

```python
class FrameRecorder:
    def __init__(self, path, fps=15, codec="mp4v", queue_frames=30): ...
    dropped = 0
    def write(self, frame_bgr, t) -> None    # returns at once
    def close(self) -> None                  # writes what is queued, then closes
```

It writes `path` and, beside it, a `.csv` with the header `frame,t` and one row per frame written.

- [ ] **Step 1: Write the failing tests.** `test_frames_and_times_are_written` (30 frames in, `close()`, then the video holds 30 frames and the CSV 30 rows with the given times), `test_write_does_not_block` (100 writes with a slow fake writer take under 50 ms, and `dropped` is 70), `test_new_frame_size_starts_a_new_file`, `test_write_error_is_survived`, `test_low_disk_turns_recording_off` (with `shutil.disk_usage` patched).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Add a frame recorder that never blocks".

### Task 2: Mission recorder

**Files:**
- Create: `droneload/mission/recorder.py`
- Modify: `droneload/mission/runner.py`, `droneload/mission/__main__.py` (`--no-record`), `droneload/flight/vehicle.py` (`Vehicle.connect(url, log_path=None)`), `.gitignore`
- Test: `tests/test_recorder.py`, `tests/test_flight.py`

**Interfaces:**
- Consumes: `FrameRecorder`, `Context`.
- Produces:

```python
class Recorder:
    def __init__(self, root="flights", plan="", cameras=("down", "forward")): ...
    folder: str
    def update(self, ctx, step_name) -> None    # once per tick: new frames, a state record every 0.2 s
    def event(self, kind, **fields) -> None     # one line in events.jsonl
    def close(self) -> None
```

`events.jsonl` lines: `{"t": 12.4, "kind": "step", "name": "hover"}`, `{"t": ..., "kind": "markers", "camera": "down", "markers": [{"id": 0, "cx": ..., "cy": ..., "offset_m": [...]}]}` when the set of confirmed IDs changes, `{"t": ..., "kind": "state", "position": [...], "attitude": [...], "height_m": ..., "battery": [...]}` every 0.2 s, and `{"kind": "abort", "reason": ...}`. `meta.json` holds the plan name, the start time, `git rev-parse HEAD`, and every calibration file's contents. `Vehicle.connect(url, log_path)` passes the path to pymavlink's `setup_logfile`, which writes each message with its timestamp, the `.tlog` format.

- [ ] **Step 1: Write the failing tests.** `test_folder_layout` (a run of the `"hover"` plan on the fake vehicle with a `SimCamera` leaves `down.mp4`, `down.csv`, `events.jsonl` and `meta.json`), `test_steps_and_markers_are_logged`, `test_state_is_logged_at_five_hertz`, `test_files_are_readable_after_a_kill` (reading the files without calling `close()` gives valid JSON lines and CSV rows), `test_folder_names_do_not_collide`, `test_no_record_writes_nothing`, and in `tests/test_flight.py`, `test_connect_writes_a_tlog` (opt-in simulator test: the file exists and `mavutil.mavlink_connection(path)` reads a heartbeat from it).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.** Recording is on by default in `python -m droneload.mission`.
- [ ] **Step 4: Run `./scripts/check.sh` and the simulator tests.**
- [ ] **Step 5: Commit.** Message "Record frames, telemetry and events for every mission run".

### Task 3: Replay

**Files:**
- Create: `testing/replay.py`
- Test: `tests/test_recorder.py`

**Interfaces:**
- Produces: `python -m testing.replay FOLDER [--camera down] [--show] [--record OUT]` reruns today's detector on the recorded frames and prints, per marker ID, the share of frames where it was confirmed then and now. `replay_frames(folder, camera) -> iterator of (t, frame)`.

- [ ] **Step 1: Write the failing tests.** `test_replay_yields_recorded_frames`, `test_replay_uses_recorded_times`, `test_replay_compares_detections` (a recording made with a marker in view reports 100% then and now).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Replay a recorded flight through the detector".

### Task 4: Measure the cost

**Files:**
- Docs: `droneload/mission/README.md` (a "Recordings" section), `README.md` and `README.fr.md` (Usage, Project Structure), `AGENTS.md` only if a rule is needed about never committing `flights/`

- [ ] **Step 1: Measure on a PC.** Run the `"pad"` plan in the simulator with and without `--no-record`; note the mean tick time, the dropped-frame count and the folder's size per minute in the log.
- [ ] **Step 2: Write the Recordings section:** what each file holds, how to open the `.tlog` in a ground station, how to replay, and the PC figures, with the companion computer's marked unverified.
- [ ] **Step 3: Run `./scripts/check.sh` and commit.** Message "Document flight recordings".

## Done When

- [ ] Every simulator run leaves a folder that `python -m testing.replay` reads.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- Measure the tick time with recording on the companion computer, and lower `RECORD_FPS` or the resolution if detection drops under its frame-rate target.
- Recorded flights replace the simulated shake baselines in `AGENTS.md` once a few exist.
