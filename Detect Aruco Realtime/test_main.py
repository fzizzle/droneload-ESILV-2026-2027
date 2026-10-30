import csv
import sys

import cv2
import numpy as np

import main
import make_test_video
from camera_opencv import OpenCVCamera

def logged_ids():
    with open(main.DETECTION_LOG, newline="") as f:
        return {int(row["id"]) for row in csv.DictReader(f)}

def test_marker_min_side():
    corner = np.array([[[0, 0], [10, 0], [10, 20], [0, 20]]], dtype=np.float32)
    assert main.marker_min_side(corner) == 10

def test_center_of():
    corner = np.array([[[0, 0], [10, 0], [10, 20], [0, 20]]], dtype=np.float32)
    assert main.center_of(corner) == (5.0, 10.0)

def test_all_project_markers_have_labels():
    assert set(main.ARUCO_LABELS) == set(range(16))

def test_source_parsing(tmp_path):
    video = tmp_path / "video.mp4"
    video.touch()

    assert OpenCVCamera("0").source == 0
    assert not OpenCVCamera("0").finite
    assert not OpenCVCamera("rtsp://camera/stream").finite
    assert OpenCVCamera(str(video)).finite
    assert OpenCVCamera("frames/%03d.jpg").finite

def test_size_filter(tmp_path, monkeypatch):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    frame = np.full((720, 1280, 3), 255, np.uint8)
    frame[100:300, 100:300] = cv2.cvtColor(cv2.aruco.generateImageMarker(aruco_dict, 0, 200), cv2.COLOR_GRAY2BGR)
    frame[100:160, 700:760] = cv2.cvtColor(cv2.aruco.generateImageMarker(aruco_dict, 1, 60), cv2.COLOR_GRAY2BGR)

    class FakeCamera:
        frames = [frame]
        finite = True

        def open(self):
            return True

        def read(self):
            return (True, self.frames.pop()) if self.frames else (False, None)

        def release(self):
            pass

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "MIN_SIDE_PX", 100)
    monkeypatch.setattr(main, "make_camera", lambda source: FakeCamera())
    monkeypatch.setattr(sys, "argv", ["main.py"])
    main.main()

    assert logged_ids() == {0}

    # The filtered marker must not be drawn on the debug image
    image = cv2.imread(main.DEBUG_IMAGE_PATH)
    green = (image[:, :, 1] > 150) & (image[:, :, 0] < 100) & (image[:, :, 2] < 100)
    assert green[90:310, 90:310].any()
    assert not green[90:170, 690:770].any()

def test_generated_video_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    make_test_video.main()
    monkeypatch.setattr(sys, "argv", ["main.py", "--source", make_test_video.OUTPUT])
    main.main()

    assert logged_ids() == set(make_test_video.MARKER_IDS)
