import csv
import math
import sys
import time

import cv2
import numpy as np
import pytest

from droneload.vision import detect, pose
from testing import make_test_video, vibration_test
from droneload.vision.camera_opencv import OpenCVCamera

def logged_ids():
    with open(detect.DETECTION_LOG, newline="") as f:
        return {int(row["id"]) for row in csv.DictReader(f)}

def write_video(path, frames, fps):
    height, width = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for frame in frames:
        writer.write(frame)
    writer.release()

def logged_rows():
    with open(detect.DETECTION_LOG, newline="") as f:
        return [(int(row["timestamp_ms"]), int(row["id"])) for row in csv.DictReader(f)]

@pytest.mark.parametrize("bad_fps", [float("nan"), float("inf"), -1.0, 0.0])
def test_opencv_camera_ignores_bad_frame_rate(tmp_path, monkeypatch, bad_fps):
    path = tmp_path / "clip.mp4"
    write_video(path, [one_marker_frame()] * 3, 30)

    class FakeCapture:
        def __init__(self, source):
            pass
        def isOpened(self):
            return True
        def get(self, prop):
            return bad_fps

    monkeypatch.setattr("droneload.vision.camera_opencv.cv2.VideoCapture", FakeCapture)
    camera = OpenCVCamera(str(path))
    assert camera.open()
    assert camera.fps == 30

def test_marker_min_side():
    corner = np.array([[[0, 0], [10, 0], [10, 20], [0, 20]]], dtype=np.float32)
    assert detect.marker_min_side(corner) == 10

def test_center_of():
    corner = np.array([[[0, 0], [10, 0], [10, 20], [0, 20]]], dtype=np.float32)
    assert detect.center_of(corner) == (5.0, 10.0)

def test_all_project_markers_have_labels():
    assert set(detect.ARUCO_LABELS) == set(range(10))
    assert detect.ARUCO_LABELS[8] == "fenetre_verso_bas"
    assert detect.ARUCO_LABELS[9] == "fenetre_verso_haut"

def test_source_parsing(tmp_path):
    video = tmp_path / "video.mp4"
    video.touch()

    assert OpenCVCamera("0").source == 0
    assert not OpenCVCamera("0").finite
    assert not OpenCVCamera("rtsp://camera/stream").finite
    assert OpenCVCamera(str(video)).finite
    assert OpenCVCamera("frames/%03d.jpg").finite

class FakeCamera:
    finite = True

    def __init__(self, frames):
        self.frames = frames

    def open(self):
        return True

    def read(self):
        return (True, self.frames.pop()) if self.frames else (False, None)

    def release(self):
        pass

def one_marker_frame():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    frame = np.full((720, 1280, 3), 255, np.uint8)
    frame[100:300, 100:300] = cv2.cvtColor(cv2.aruco.generateImageMarker(aruco_dict, 0, 200), cv2.COLOR_GRAY2BGR)
    return frame

@pytest.mark.parametrize("argv, expected", [(["detect"], set()), (["detect", "--no-track"], {0})])
def test_single_frame_needs_no_track(tmp_path, monkeypatch, argv, expected):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([one_marker_frame()]))
    monkeypatch.setattr(sys, "argv", argv)
    detect.main()

    assert logged_ids() == expected

def test_size_filter(tmp_path, monkeypatch):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    frame = np.full((720, 1280, 3), 255, np.uint8)
    frame[100:300, 100:300] = cv2.cvtColor(cv2.aruco.generateImageMarker(aruco_dict, 0, 200), cv2.COLOR_GRAY2BGR)
    frame[100:160, 700:760] = cv2.cvtColor(cv2.aruco.generateImageMarker(aruco_dict, 1, 60), cv2.COLOR_GRAY2BGR)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "MIN_SIDE_PX", 100)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([frame]))
    monkeypatch.setattr(sys, "argv", ["detect", "--no-track"])
    detect.main()

    assert logged_ids() == {0}

    # The filtered marker must not be drawn on the debug image
    image = cv2.imread(detect.DEBUG_IMAGE_PATH)
    green = (image[:, :, 1] > 150) & (image[:, :, 0] < 100) & (image[:, :, 2] < 100)
    assert green[90:310, 90:310].any()
    assert not green[90:170, 690:770].any()

def test_generated_video_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    make_test_video.main()
    monkeypatch.setattr(sys, "argv", ["detect", "--source", make_test_video.OUTPUT])
    detect.main()

    assert logged_ids() == set(make_test_video.MARKER_IDS)

    # The debug image must show confirmed markers even when the video is short
    image = cv2.imread(detect.DEBUG_IMAGE_PATH)
    green = (image[:, :, 1] > 150) & (image[:, :, 0] < 100) & (image[:, :, 2] < 100)
    assert green.any()

def test_vibration_helpers():
    frame = vibration_test.make_frame(120)
    detector = detect.make_detector()

    assert vibration_test.is_found(frame, detector)
    assert vibration_test.motion_blur(frame, 0, 0) is frame
    assert vibration_test.motion_blur(frame, 10, 45).shape == frame.shape
    assert vibration_test.rolling_wobble(frame, 10, 0).shape == frame.shape
    assert vibration_test.blur_rate(frame, 0, detector) == 1.0
    assert vibration_test.blur_rate(frame, 40, detector) < 1.0

CAMERA_MATRIX = np.array([[900, 0, 640], [0, 900, 360], [0, 0, 1]], dtype=np.float64)
NO_DISTORTION = np.zeros(5)

def render_marker(position_m):
    """Render a 20 cm marker facing the camera, and return the image."""
    side = 600
    marker = cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), 0, side)
    half = pose.MARKER_SIZE_M / 2
    points = np.array([[-half, -half, 0], [half, -half, 0], [half, half, 0], [-half, half, 0]], dtype=np.float32)
    corners, _ = cv2.projectPoints(points, np.zeros(3), np.array(position_m, dtype=np.float64),
                                   CAMERA_MATRIX, NO_DISTORTION)
    source = np.array([[0, 0], [side, 0], [side, side], [0, side]], dtype=np.float32)
    warp = cv2.getPerspectiveTransform(source, corners.reshape(4, 2).astype(np.float32))
    return cv2.warpPerspective(marker, warp, (1280, 720), borderValue=255)

def test_marker_offset_from_exact_corners():
    half = pose.MARKER_SIZE_M / 2
    points = np.array([[-half, -half, 0], [half, -half, 0], [half, half, 0], [-half, half, 0]], dtype=np.float32)
    corners, _ = cv2.projectPoints(points, np.zeros(3), np.array([0.1, -0.2, 1.5]), CAMERA_MATRIX, NO_DISTORTION)
    offset = pose.marker_offset(corners.reshape(1, 4, 2).astype(np.float32), CAMERA_MATRIX, NO_DISTORTION)

    assert offset == pytest.approx((0.1, -0.2, 1.5), abs=0.001)

def test_marker_offset_from_detected_image():
    for position in [(0.0, 0.0, 1.0), (0.3, -0.1, 1.5), (-0.4, 0.2, 2.5)]:
        corners, ids, _ = detect.make_detector().detectMarkers(render_marker(position))
        assert ids is not None and ids[0][0] == 0
        offset = pose.marker_offset(corners[0], CAMERA_MATRIX, NO_DISTORTION)
        assert offset == pytest.approx(position, abs=0.02 * position[2])

def test_load_calibration(tmp_path):
    path = tmp_path / "camera.yaml"
    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    storage.write("camera_matrix", CAMERA_MATRIX)
    storage.write("dist_coeffs", NO_DISTORTION)
    storage.release()

    matrix, coeffs = pose.load_calibration(path)
    assert np.array_equal(matrix, CAMERA_MATRIX)
    assert coeffs.size == 5

def green_mask(image):
    return (image[:, :, 1] > 150) & (image[:, :, 0] < 100) & (image[:, :, 2] < 100)

def test_record_writes_annotated_video(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    make_test_video.main()
    monkeypatch.setattr(sys, "argv", ["detect", "--source", make_test_video.OUTPUT, "--record", "out.mp4"])
    detect.main()

    video = cv2.VideoCapture("out.mp4")
    frames = []
    while True:
        ok, frame = video.read()
        if not ok:
            break
        frames.append(frame)
    assert len(frames) == 150
    assert green_mask(frames[-1]).any()

def test_unconfirmed_markers_drawn_grey(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([one_marker_frame()]))
    monkeypatch.setattr(sys, "argv", ["detect"])
    detect.main()

    image = cv2.imread(detect.DEBUG_IMAGE_PATH)
    grey = (np.abs(image.astype(int) - detect.REJECTED_COLOR).sum(axis=2) < 30)
    assert grey[90:310, 90:310].any()
    assert not green_mask(image)[90:310, 90:310].any()

def test_status_line_drawn(tmp_path, monkeypatch):
    blank = np.full((720, 1280, 3), 255, np.uint8)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([blank]))
    monkeypatch.setattr(sys, "argv", ["detect"])
    detect.main()

    assert (cv2.imread(detect.DEBUG_IMAGE_PATH)[:60, :400] < 200).any()

def test_show_displays_frames_until_q(tmp_path, monkeypatch):
    shown = []
    keys = iter([-1, ord("q"), -1])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([one_marker_frame()] * 3))
    monkeypatch.setattr(detect.cv2, "imshow", lambda name, image: shown.append(image))
    monkeypatch.setattr(detect.cv2, "waitKey", lambda delay: next(keys))
    monkeypatch.setattr(detect.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(sys, "argv", ["detect", "--show"])
    detect.main()

    assert len(shown) == 2

def test_shake_rates_on_footage():
    frames = [vibration_test.make_frame(240)] * 15
    detector = detect.make_detector()
    clean = vibration_test.SHAKE_LEVELS["clean"]

    shaken, move, _ = vibration_test.shake_frame(frames[0], (0, 0, 0), (0, 0, 0), clean, 1.0, 0)
    assert move == 0 and (shaken == frames[0]).all()

    real, rates = vibration_test.shake_rates(frames, detector)
    assert real == {vibration_test.MARKER_ID}
    assert rates["clean"]["raw"] == 1.0 and rates["clean"]["move_px"] == 0
    assert rates["severe"]["move_px"] > rates["mild"]["move_px"] > 0
    assert rates["severe"]["tracked"] < rates["clean"]["tracked"]

def test_write_shaken(tmp_path):
    frames = [vibration_test.make_frame(240)] * 5
    path = str(tmp_path / "shaken.mp4")
    vibration_test.write_shaken(frames, 30, vibration_test.SHAKE_LEVELS["severe"], path)

    written, fps = vibration_test.read_frames(path)
    assert len(written) == 5 and fps == 30
    assert written[0].shape == frames[0].shape

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

def test_shake_path_seed():
    level = vibration_test.SHAKE_LEVELS["moderate"]
    default = vibration_test.shake_path(50, level, 1.0)
    assert (default == vibration_test.shake_path(50, level, 1.0, seed=vibration_test.SEED)).all()
    assert not (default == vibration_test.shake_path(50, level, 1.0, seed=2)).all()

def test_loop_does_not_sleep_between_frames(tmp_path, monkeypatch):
    slept = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect.time, "sleep", slept.append)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera([one_marker_frame()] * 3))
    monkeypatch.setattr(sys, "argv", ["detect"])
    detect.main()

    assert slept == []

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

@pytest.mark.parametrize("name", ["DICT_NOPE", "dict_4x4_50"])
def test_unknown_dict_rejected_before_camera_opens(monkeypatch, name):
    opened = []
    monkeypatch.setattr(detect, "make_camera", opened.append)
    monkeypatch.setattr(sys, "argv", ["detect", "--dict", name])
    with pytest.raises(SystemExit) as error:
        detect.main()

    assert error.value.code == 2
    assert opened == []


def test_detector_uses_default_polygon_accuracy():
    params = detect.make_detector().getDetectorParameters()
    assert params.polygonalApproxAccuracyRate == pytest.approx(0.03)

def test_show_delay_ms():
    assert detect.show_delay_ms(1.1, 1.0) == 100      # hold the frame until the next one is due
    assert detect.show_delay_ms(1.0, 1.05) == 1       # behind schedule: waitKey still needs 1 ms
    assert detect.show_delay_ms(1.0004, 1.0) == 1

def run_show(tmp_path, monkeypatch, camera):
    delays = []

    def wait_key(delay):
        delays.append(delay)
        time.sleep(delay / 1000)
        return -1

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(detect, "make_camera", lambda source: camera)
    monkeypatch.setattr(detect.cv2, "imshow", lambda name, image: None)
    monkeypatch.setattr(detect.cv2, "waitKey", wait_key)
    monkeypatch.setattr(detect.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(sys, "argv", ["detect", "--show"])
    start = time.perf_counter()
    detect.main()
    return delays, time.perf_counter() - start

def test_show_plays_video_files_at_their_speed(tmp_path, monkeypatch):
    camera = FakeCamera([one_marker_frame()] * 3)
    camera.fps = 20                                    # 50 ms per frame: 3 frames last 0.15 s
    delays, elapsed = run_show(tmp_path, monkeypatch, camera)

    assert len(delays) == 3
    assert max(delays) > 1
    assert all(1 <= delay <= 50 for delay in delays)
    assert elapsed >= 0.14

def test_show_does_not_slow_live_cameras(tmp_path, monkeypatch):
    delays, _ = run_show(tmp_path, monkeypatch, LiveCamera([one_marker_frame()] * 3))

    assert delays == [1, 1, 1]
