# Checkerboard camera calibration. Writes the file pose.load_calibration() reads:
#   python -m droneload.vision.calibrate --source 0
import cv2
import numpy as np

# Calibration settings
BOARD_INNER_CORNERS = (9, 6)       # inner corners per row and column: a 10 x 7 square board
SQUARE_SIZE_M       = 0.025        # measure the printed square and pass it with --square
TARGET_FRAMES       = 20           # frames to keep before calibrating
MIN_FRAMES          = 10           # fewer than this gives an unreliable calibration
MIN_GAP_FRAMES      = 15           # frames skipped between kept frames, so views differ
MAX_RMS_PX          = 1.0          # above this, warn that the calibration is poor
OUTPUT_PATH         = "camera.yaml"

def board_points(inner_corners, square_size_m):
    """Board corners in metres, z = 0, in the order find_board() returns them."""
    cols, rows = inner_corners
    grid = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_size_m
    return np.hstack([grid, np.zeros((len(grid), 1))]).astype(np.float32)

def find_board(gray, inner_corners):
    """Return the board's inner corners as an (N, 1, 2) float32 array, or None."""
    found, corners = cv2.findChessboardCornersSB(gray, inner_corners)
    if not found:
        return None
    return corners.reshape(-1, 1, 2).astype(np.float32)

def calibrate(image_points, image_size, inner_corners, square_size_m):
    """Return (camera_matrix, dist_coeffs, rms_px). image_size is (width, height)."""
    if len(image_points) < MIN_FRAMES:
        raise ValueError(f"Found the board in {len(image_points)} frames; need at least {MIN_FRAMES}")
    object_points = [board_points(inner_corners, square_size_m)] * len(image_points)
    rms, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(object_points, image_points,
                                                                image_size, None, None)
    return camera_matrix, dist_coeffs, float(rms)

def save_calibration(path, camera_matrix, dist_coeffs, image_size, rms_px):
    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    storage.write("camera_matrix", camera_matrix)
    storage.write("dist_coeffs", np.asarray(dist_coeffs, dtype=np.float64))
    storage.write("image_width", int(image_size[0]))
    storage.write("image_height", int(image_size[1]))
    storage.write("rms_px", float(rms_px))
    storage.release()
