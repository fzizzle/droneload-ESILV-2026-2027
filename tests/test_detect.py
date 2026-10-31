import csv
import sys

import cv2
import numpy as np
import pytest

from droneload.vision import detect, pose
from testing import make_test_video, vibration_test
from droneload.vision.camera_opencv import OpenCVCamera

def logged_ids():
    with open(detect.DETECTION_LOG, newline="") as f:
        return {int(row["id"]) for row in csv.DictReader(f)}

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
    monkeypatch.setattr(detect, "MIN_SIDE_PX", 100)
    monkeypatch.setattr(detect, "make_camera", lambda source: FakeCamera())
    monkeypatch.setattr(sys, "argv", ["detect"])
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
