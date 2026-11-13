# Checkerboard camera calibration. Writes the file pose.load_calibration() reads:
#   python -m droneload.vision.calibrate --source 0
import argparse
import time

import cv2
import numpy as np

from .detect import make_camera

# Calibration settings
BOARD_INNER_CORNERS = (9, 6)       # inner corners per row and column: a 10 x 7 square board
SQUARE_SIZE_M       = 0.025        # measure the printed square and pass it with --square
TARGET_FRAMES       = 20           # frames to keep before calibrating
MIN_FRAMES          = 10           # fewer than this gives an unreliable calibration
MIN_MOVE_PX         = 20.0         # mean corner shift from every kept frame, so views differ
MAX_RMS_PX          = 1.0          # above this, warn that the calibration is poor
MIN_TILT_SPREAD_DEG = 20.0         # below this angle between board orientations, warn
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
    """Return (camera_matrix, dist_coeffs, rms_px, tilt_spread_deg). image_size is (width, height).

    tilt_spread_deg is the largest angle between the board's orientations in two views.
    Views of parallel boards give a wrong focal length with a low RMS, so check both.
    """
    if len(image_points) < MIN_FRAMES:
        raise ValueError(f"Found the board in {len(image_points)} frames; need at least {MIN_FRAMES}")
    object_points = [board_points(inner_corners, square_size_m)] * len(image_points)
    rms, camera_matrix, dist_coeffs, rvecs, _ = cv2.calibrateCamera(object_points, image_points,
                                                                    image_size, None, None)
    return camera_matrix, dist_coeffs, float(rms), tilt_spread(rvecs)

def tilt_spread(rvecs):
    """Largest angle in degrees between the board's normals in any two views."""
    normals = np.array([cv2.Rodrigues(r)[0][:, 2] for r in rvecs])
    cosines = np.clip(normals @ normals.T, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosines.min())))

def save_calibration(path, camera_matrix, dist_coeffs, image_size, rms_px):
    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    storage.write("camera_matrix", camera_matrix)
    storage.write("dist_coeffs", np.asarray(dist_coeffs, dtype=np.float64))
    storage.write("image_width", int(image_size[0]))
    storage.write("image_height", int(image_size[1]))
    storage.write("rms_px", float(rms_px))
    storage.release()

def parse_board(text):
    cols, rows = text.lower().split("x")
    return int(cols), int(rows)

def is_new_view(corners, kept):
    """True if the board moved at least MIN_MOVE_PX from every kept frame."""
    return all(np.linalg.norm(corners - k, axis=2).mean() >= MIN_MOVE_PX for k in kept)

def capture(camera, inner_corners, target):
    """Keep frames that show the board in a new position. Return (points, size, found_any)."""
    image_points, image_size, found_any = [], None, False
    try:
        while len(image_points) < target:
            ok, frame = camera.read()
            if not ok or frame is None:
                if getattr(camera, "finite", False):
                    break
                time.sleep(0.05)
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
            corners = find_board(gray, inner_corners)
            if corners is None:
                continue
            found_any = True
            if not is_new_view(corners, image_points):
                continue
            image_points.append(corners)
            image_size = (gray.shape[1], gray.shape[0])
            print(f"[INFO] captured {len(image_points)}/{target}", flush=True)
    except KeyboardInterrupt:
        print("\n[INFO] Capture stopped; calibrating with the frames kept.")
    return image_points, image_size, found_any

def main():
    parser = argparse.ArgumentParser(description="Calibrate a camera with a printed checkerboard")
    parser.add_argument("--source", default="0", help="camera source, as for droneload.vision (default: 0)")
    parser.add_argument("--board", default="x".join(map(str, BOARD_INNER_CORNERS)),
                        help="inner corners per row and column (default: %(default)s)")
    parser.add_argument("--square", type=float, default=SQUARE_SIZE_M,
                        help="measured square size in metres (default: %(default)s)")
    parser.add_argument("--frames", type=int, default=TARGET_FRAMES,
                        help="frames to keep (default: %(default)s)")
    parser.add_argument("--output", default=OUTPUT_PATH, help="calibration file (default: %(default)s)")
    args = parser.parse_args()
    inner_corners = parse_board(args.board)

    camera = make_camera(args.source)
    if not camera.open():
        print("[ERROR] Camera failed to open. Exiting.")
        exit(1)
    print("[INFO] Move and tilt the board across the whole image. Press Ctrl+C to stop early.")
    try:
        image_points, image_size, found_any = capture(camera, inner_corners, args.frames)
    finally:
        camera.release()

    try:
        camera_matrix, dist_coeffs, rms, spread = calibrate(image_points, image_size, inner_corners, args.square)
    except ValueError as error:
        if found_any:
            print(f"[ERROR] {error}. Move and tilt the board to more positions.")
        else:
            print(f"[ERROR] {error}. Check that the board has {args.board} inner corners and is in view.")
        exit(1)

    save_calibration(args.output, camera_matrix, dist_coeffs, image_size, rms)
    print(f"[INFO] RMS error {rms:.2f} px from {len(image_points)} frames at {image_size[0]} x {image_size[1]}")
    print(f"[INFO] fx={camera_matrix[0, 0]:.1f} fy={camera_matrix[1, 1]:.1f} "
          f"cx={camera_matrix[0, 2]:.1f} cy={camera_matrix[1, 2]:.1f}")
    if rms > MAX_RMS_PX:
        print(f"[WARNING] RMS error is above {MAX_RMS_PX} px. Recalibrate with sharper frames and more tilt.")
    if spread < MIN_TILT_SPREAD_DEG:
        print(f"[WARNING] The board was only tilted {spread:.0f}° between views. "
              "Recalibrate, tilting it in several directions, up to about 45°.")
    print(f"[INFO] Calibration saved to {args.output}")

if __name__ == "__main__":
    main()
