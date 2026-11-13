import cv2
import numpy as np
import pytest

from droneload.vision import calibrate, pose

CAMERA_MATRIX = np.array([[900, 0, 640], [0, 900, 360], [0, 0, 1]], dtype=np.float64)
NO_DISTORTION = np.zeros(5)
IMAGE_SIZE    = (1280, 720)
SQUARE_M      = 0.025
SQUARES       = (10, 7)   # 9 x 6 inner corners
SQUARE_PX     = 60        # pixels per square in the flat board image

def flat_board():
    """The board with a one-square white margin, and its outer corners in metres."""
    cols, rows = SQUARES[0] + 2, SQUARES[1] + 2
    image = np.full((rows * SQUARE_PX, cols * SQUARE_PX), 255, np.uint8)
    for r in range(SQUARES[1]):
        for c in range(SQUARES[0]):
            if (r + c) % 2 == 0:
                y, x = (r + 1) * SQUARE_PX, (c + 1) * SQUARE_PX
                image[y:y + SQUARE_PX, x:x + SQUARE_PX] = 0
    # Board coordinates start at the first inner corner, one square in from the board's edge
    left, top = -2 * SQUARE_M, -2 * SQUARE_M
    right, bottom = left + cols * SQUARE_M, top + rows * SQUARE_M
    outer = np.array([[left, top, 0], [right, top, 0], [right, bottom, 0], [left, bottom, 0]], dtype=np.float32)
    return image, outer

def project_outer(rvec, tvec):
    _, outer = flat_board()
    points, _ = cv2.projectPoints(outer, rvec, tvec, CAMERA_MATRIX, NO_DISTORTION)
    return points.reshape(4, 2).astype(np.float32)

def render_board(rvec, tvec):
    image, _ = flat_board()
    h, w = image.shape
    source = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    warp = cv2.getPerspectiveTransform(source, project_outer(rvec, tvec))
    return cv2.warpPerspective(image, warp, IMAGE_SIZE, borderValue=255)

def views(n):
    rng = np.random.default_rng(0)
    result = []
    while len(result) < n:
        rvec = np.array([rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)])
        tvec = np.array([rng.uniform(-0.05, 0.05) - 0.1, rng.uniform(-0.03, 0.03) - 0.06, rng.uniform(0.4, 0.7)])
        corners = project_outer(rvec, tvec)
        inside = ((corners[:, 0] > 40) & (corners[:, 0] < IMAGE_SIZE[0] - 40) &
                  (corners[:, 1] > 40) & (corners[:, 1] < IMAGE_SIZE[1] - 40)).all()
        if inside:
            result.append((rvec, tvec))
    return result

def found_corners(n):
    return [calibrate.find_board(render_board(r, t), calibrate.BOARD_INNER_CORNERS) for r, t in views(n)]

def test_board_points_shape_and_spacing():
    points = calibrate.board_points((9, 6), 0.025)
    assert points.shape == (54, 3)
    assert points[1] - points[0] == pytest.approx((0.025, 0, 0))
    assert (points[:, 2] == 0).all()

def test_find_board_on_rendered_view():
    rvec, tvec = views(1)[0]
    corners = calibrate.find_board(render_board(rvec, tvec), (9, 6))
    assert corners is not None and corners.shape == (54, 1, 2)

def test_find_board_none_on_blank():
    assert calibrate.find_board(np.full((720, 1280), 255, np.uint8), (9, 6)) is None

def test_calibrate_recovers_known_camera():
    corners = found_corners(15)
    assert all(c is not None for c in corners)
    matrix, _, rms = calibrate.calibrate(corners, IMAGE_SIZE, (9, 6), SQUARE_M)
    assert matrix[0, 0] == pytest.approx(900, rel=0.02)
    assert matrix[1, 1] == pytest.approx(900, rel=0.02)
    assert matrix[0, 2] == pytest.approx(640, abs=10)
    assert matrix[1, 2] == pytest.approx(360, abs=10)
    assert rms < 0.5

def test_calibrate_rejects_too_few_frames():
    with pytest.raises(ValueError, match=r"5.*10|10.*5"):
        calibrate.calibrate(found_corners(5), IMAGE_SIZE, (9, 6), SQUARE_M)

def test_saved_calibration_loads_in_pose(tmp_path):
    path = tmp_path / "camera.yaml"
    calibrate.save_calibration(path, CAMERA_MATRIX, NO_DISTORTION, IMAGE_SIZE, 0.3)

    matrix, coeffs = pose.load_calibration(path)
    assert np.array_equal(matrix, CAMERA_MATRIX)
    assert coeffs.size == 5
    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    assert storage.getNode("image_width").real() == 1280
    assert storage.getNode("image_height").real() == 720
    assert storage.getNode("rms_px").real() == pytest.approx(0.3)
