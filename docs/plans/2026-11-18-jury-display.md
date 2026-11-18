# Jury Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the drone's automatic detections on the organisers' screen during the run. The rules require this for every scored action, so no flight point counts without it.

**Architecture:** Two channels, because the venue's network is unknown. The first is text: the mission sends one short line per event through the flight controller, which forwards it over the kit's 433 MHz telemetry radio to any ground station on a laptop. It needs no Wi-Fi and no ground software of ours. The second is video: the companion computer serves the annotated camera image as an MJPEG stream that a laptop's browser opens, when Wi-Fi is allowed. The laptop's screen output goes to the organisers' screen.

**Tech Stack:** `pymavlink` (already used), the standard library's `http.server` and `threading`, OpenCV for JPEG encoding. No new dependency.

**Spec:** `docs/contest-rules.md`, Drone Requirements ("annotated video, text or similar"); `droneload/mission/README.md` ("Display delay: under half a second on a laptop").

## Global Constraints

- Needs these plans merged: `vision-api` (for `annotate`), `flight-velocity`, `mission-runner`.
- Only `flight` talks to the flight controller, so the text line goes through a new `Vehicle.say()`. This is flight controller code and needs the project lead's OK; it sends a status message, not a command.
- `STATUSTEXT` holds 50 characters. Lines are cut to fit, never split.
- The text channel is limited to `SAY_PER_SECOND = 2`, so it cannot crowd the telemetry link.
- The display never blocks the mission tick. A slow or absent viewer costs the tick nothing.
- The stream is read-only: the page has no control, in keeping with "the operator may only confirm".
- Settings are constants at the top of `droneload/mission/display.py`: `STREAM_PORT = 8080`, `STREAM_FPS = 10`, `STREAM_WIDTH = 640`, `JPEG_QUALITY = 60`.
- **Unverified until tried on the kit:** that ArduPilot forwards a companion's `STATUSTEXT` to the telemetry radio, and the delay over that link. Task 1 checks forwarding in the simulator with two connections.
- Branch `feature/jury-display`, log `logs/YYYY-MM-DD-feature-jury-display.md`. Run `source .venv/bin/activate` before `./scripts/check.sh`.

## Review Focus

1. **Same detection every tick:** a marker in view for 10 s must produce one line when it appears and one when the step uses it, not 200. Test `test_repeated_detection_is_said_once` (Task 2).
2. **More events than the rate allows:** the newest lines win and the count dropped is appended to the next line sent. Test `test_rate_limit_keeps_the_newest` (Task 1).
3. **Accents and long labels:** `zone_de_decollage` fits; text is ASCII-folded and cut at 50 bytes. Test `test_text_is_cut_to_fifty_bytes` (Task 1).
4. **Viewer disconnects mid-frame:** the server thread survives and the next viewer connects. Test `test_viewer_disconnect_is_harmless` (Task 3).
5. **Port already in use:** the mission starts anyway, with one warning, and the text channel still works. Test `test_busy_port_does_not_stop_the_mission` (Task 3).

---

### Task 1: Text lines through the flight controller

**Files:**
- Modify: `droneload/flight/vehicle.py`
- Test: `tests/test_flight.py`, `tests/test_flight_sitl.py`

**Interfaces:**
- Produces: `vehicle.say(text) -> None`. It queues the line; `poll()` sends at most `SAY_PER_SECOND` lines per second as `STATUSTEXT` with severity `MAV_SEVERITY_INFO`. `KinematicVehicle` gains the same method and a `said` list.

- [ ] **Step 1: Write the failing tests.** `test_say_sends_statustext`, `test_text_is_cut_to_fifty_bytes`, `test_rate_limit_keeps_the_newest` (10 lines queued in one tick: the first second sends the 2 newest, and the second of them ends with `(+8)`), and the opt-in simulator test `test_statustext_reaches_a_second_connection`: a second `mavutil` connection to the simulator's second port (`tcp:127.0.0.1:5762`) receives the line.
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the unit and simulator tests.** If the simulator does not forward the line, stop and record it in the log: the text channel then needs a ground program of ours on a separate radio, which is a decision for the project lead.
- [ ] **Step 5: Commit.** Message "Send short status lines through the flight controller".

### Task 2: What to say

**Files:**
- Create: `droneload/mission/display.py`
- Modify: `droneload/mission/runner.py` (call the display once per tick)
- Test: `tests/test_display.py`

**Interfaces:**
- Consumes: `Context`, `Vehicle.say`.
- Produces:

```python
class Display:
    def __init__(self, say, stream=None): ...
    def update(self, ctx, step_name) -> None     # once per tick
    def event(self, text) -> None                # for steps: "DROP target 3", "ROBOT aligned 1"
    def status_line(self) -> str                 # what annotate() draws on the image
```

Lines, all upper-case keywords first so a jury can read them at a glance: `STEP <name>` on each step change, `SEE <id> <label>` when a marker is first confirmed and again after it has been gone 5 s, `SEE target <n>` and `SEE path` likewise, `ABORT <reason>`, `DONE`.

- [ ] **Step 1: Write the failing tests.** `test_step_change_is_said`, `test_new_marker_is_said`, `test_repeated_detection_is_said_once`, `test_marker_is_said_again_after_a_gap`, `test_events_pass_through`, and `test_runner_updates_the_display` (a run of the `"hover"` plan on the fake vehicle says `STEP arm`, `STEP take-off`, `STEP hover`, `STEP land`, `DONE`, in order).
- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement.** `run()` gains `display=None`.
- [ ] **Step 4: Run the tests.**
- [ ] **Step 5: Commit.** Message "Say steps and detections on the jury display".

### Task 3: Video stream

**Files:**
- Create: `droneload/mission/stream.py`
- Modify: `droneload/mission/display.py`, `droneload/mission/__main__.py` (`--stream`)
- Test: `tests/test_display.py`
- Docs: `droneload/mission/README.md` (a "Jury display" section with the setup at the venue), `README.md` and `README.fr.md` (Usage), `docs/mission-map.md` ("Show detections on the organisers' screen"), `TODO.md` ("Detection display for the jury")

**Interfaces:**
- Produces:

```python
class Stream:
    def __init__(self, port=STREAM_PORT): ...
    def start(self) -> bool           # False, with one warning, if the port is busy
    def show(self, frame_bgr) -> None # keeps only the newest frame; returns at once
    def stop(self) -> None
```

`GET /` returns a page with one `<img src="/video">` filling the window and the last 8 text lines under it. `GET /video` is `multipart/x-mixed-replace` JPEG at `STREAM_FPS`. `Display.update` calls `show(annotate(frame, marker_frame, status_line()))` for the `"down"` camera, or `"forward"` when the current step names it. JPEG encoding happens in the server thread, not in the tick.

- [ ] **Step 1: Write the failing tests,** against a server on port 0 (any free port) with `urllib.request`.

  - `test_page_is_served`: `GET /` is 200 and contains `/video`.
  - `test_video_serves_jpegs`: the first part read from `/video` decodes with `cv2.imdecode` to a 640-wide image.
  - `test_show_does_not_block`: 100 calls to `show` with no viewer take under 50 ms in total.
  - `test_viewer_disconnect_is_harmless`, `test_busy_port_does_not_stop_the_mission`: as in Review Focus.
  - `test_stop_frees_the_port`.

- [ ] **Step 2: Run them and check they fail.**
- [ ] **Step 3: Implement** with `http.server.ThreadingHTTPServer` on a daemon thread.
- [ ] **Step 4: Run `./scripts/check.sh`.** Then run the `"hover"` plan in the simulator with `--stream`, open `http://127.0.0.1:8080`, and note the delay seen in the log.
- [ ] **Step 5: Update the docs listed above and commit.** Message "Stream the annotated camera image for the jury".

## Done When

- [ ] A ground station connected to the simulator shows the mission's lines, and a browser shows the annotated video.
- [ ] `./scripts/check.sh` passes, docs are updated and the pull request is open.

## After This Plan

- On the kit: measure the text delay over the 433 MHz radio, and the video delay over Wi-Fi from the companion computer, with the motors running.
- Ask the organisers how a team's laptop connects to their screen, and whether Wi-Fi is allowed. If it is not, the text channel is the display; rehearse with it alone.
