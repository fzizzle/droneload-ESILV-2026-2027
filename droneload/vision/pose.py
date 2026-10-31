import cv2
import numpy as np

MARKER_SIZE_M = 0.20

def load_calibration(path):
    """Read camera_matrix and dist_coeffs from an OpenCV YAML file."""
    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    if not storage.isOpened():
        raise FileNotFoundError(f"Cannot open calibration file: {path}")
    camera_matrix = storage.getNode("camera_matrix").mat()
    dist_coeffs   = storage.getNode("dist_coeffs").mat()
    storage.release()
    return camera_matrix, dist_coeffs

def marker_offset(corner, camera_matrix, dist_coeffs, marker_size_m=MARKER_SIZE_M):
    """Return the marker centre in metres, in the camera frame: x right, y down, z forward."""
    half = marker_size_m / 2
    object_points = np.array([[-half,  half, 0],
                              [ half,  half, 0],
                              [ half, -half, 0],
                              [-half, -half, 0]], dtype=np.float32)
    found, _, translation = cv2.solvePnP(object_points, corner[0], camera_matrix, dist_coeffs,
                                         flags=cv2.SOLVEPNP_IPPE_SQUARE)
    if not found:
        return None
    return tuple(float(value) for value in translation.flatten())
