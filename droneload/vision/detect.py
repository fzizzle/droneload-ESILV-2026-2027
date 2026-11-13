from .camera_opencv import OpenCVCamera
from .tracking.tracker import MarkerTracker
import argparse
import cv2
import csv
import time
import os
import numpy as np

# ArUco settings 
ARUCO_DICT        = "DICT_4X4_50"
MIN_SIDE_PX       = 10
DETECTION_LOG     = "detections.csv"
WRITE_COOLDOWN_MS = 1000
DEBUG_IMAGE_PATH  = "aruco_debug.jpg"
SAVE_EVERY_SEC    = 2.0
LOG_EVERY_SEC     = 2.0
SHOW_WINDOW       = "droneload"
RECORD_FPS        = 30
RECORD_CODEC      = "mp4v"
REJECTED_COLOR    = (128, 128, 128)  # markers the tracker has not confirmed
CLAHE             = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# labels
ARUCO_LABELS = {
    0:  "zone_de_decollage",
    1:  "robot",
    2:  "align",
    3:  "align",
    4:  "fenetre_recto_droite_bas",
    5:  "fenetre_recto_droite_haut",
    6:  "fenetre_recto_gauche_haut",
    7:  "fenetre_recto_gauche_bas",
    8:  "fenetre_verso_bas",
    9:  "fenetre_verso_haut",
}

#  Helpers 
def now_ms() -> int:
    return int(time.time() * 1000)

def preprocess(gray: np.ndarray) -> np.ndarray:
    """CLAHE adaptive contrast enhancement for variable lighting."""
    return CLAHE.apply(gray)

def make_detector(dict_name: str = ARUCO_DICT) -> cv2.aruco.ArucoDetector:
    aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dict_name))
    params = cv2.aruco.DetectorParameters()

    # Adaptive threshold range - handles bright/dark scenes
    params.adaptiveThreshWinSizeMin  = 3
    params.adaptiveThreshWinSizeMax  = 53
    params.adaptiveThreshWinSizeStep = 10
    params.adaptiveThreshConstant    = 7

    # Allow smaller markers (useful when drone is higher)
    params.minMarkerPerimeterRate      = 0.02
    params.polygonalApproxAccuracyRate = 0.05

    return cv2.aruco.ArucoDetector(aruco_dict, params)

def marker_min_side(corner) -> float:
    pts   = corner[0]
    sides = [float(cv2.norm(pts[i] - pts[(i + 1) % 4])) for i in range(4)]
    return min(sides)

def center_of(corner):
    pts = corner[0]
    return round(float(pts[:, 0].mean()), 1), round(float(pts[:, 1].mean()), 1)

def init_csv(path):
    exists = os.path.isfile(path)
    f      = open(path, "a", newline="")
    writer = csv.writer(f)
    if not exists:
        writer.writerow(["timestamp_ms", "id", "label", "cx", "cy"])
        f.flush()
    return f, writer

def print_detections(detect_ms, detected_info):
    print(f"\n[{time.strftime('%H:%M:%S')}] detect={detect_ms:.1f}ms")
    if detected_info:
        for mid, label, cx, cy in detected_info:
            print(f"  ID={mid:>2}  label={label:<40}  center=({cx},{cy})")
    else:
        print("  No markers detected.")

def draw_status(vis, detect_ms, fps, confirmed, rejected):
    """Draw detection time, frame rate and marker counts in the top-left corner."""
    text = f"detect {detect_ms:.1f} ms  {fps:.0f} fps  confirmed {confirmed}  rejected {rejected}"
    cv2.rectangle(vis, (0, 0), (520, 36), (0, 0, 0), -1)
    cv2.putText(vis, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

def make_camera(source):
    if source == "rubikpi-csi":
        from .camera_rubikpi_csi import RubikPiCSICamera
        return RubikPiCSICamera(camera=0, size=(1280, 720), fps=30)
    if source == "picamera":
        from .camera_picamera2 import PiCamera2Source
        return PiCamera2Source(size=(1280, 720))
    return OpenCVCamera(source, size=(1280, 720), fps=30)

# Main
def main():
    parser = argparse.ArgumentParser(description="Real-time ArUco marker detection")
    parser.add_argument("--source", default="0",
                        help="rubikpi-csi, picamera, or anything cv2.VideoCapture opens: "
                             "device index, video file, image sequence, GStreamer pipeline "
                             "(default: 0)")
    parser.add_argument("--dict", default=ARUCO_DICT,
                        help=f"cv2.aruco dictionary name (default: {ARUCO_DICT})")
    parser.add_argument("--no-track", action="store_true",
                        help="report every detection, without confirming it across frames")
    parser.add_argument("--show", action="store_true",
                        help="show the annotated video in a window; press q to stop")
    parser.add_argument("--record", metavar="FILE",
                        help="save the annotated video to FILE, e.g. out.mp4")
    args = parser.parse_args()

    camera = make_camera(args.source)
    if not camera.open():
        print("[ERROR] Camera failed to open. Exiting.")
        exit(1)

    detector         = make_detector(args.dict)
    tracker          = None if args.no_track else MarkerTracker()
    csv_file, writer = init_csv(DETECTION_LOG)
    last_written     = {}
    last_save        = 0.0
    last_log         = 0.0
    last_frame       = None
    recorder         = None
    last_tick        = None
    fps              = 0.0

    print("[INFO] Starting detection loop... Press Ctrl+C to stop.")

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                if getattr(camera, "finite", False):
                    # Show the last frame, since tracking hides the first one
                    if last_frame is not None:
                        print_detections(*last_frame[:2])
                        cv2.imwrite(DEBUG_IMAGE_PATH, last_frame[2])
                    print("[INFO] End of source.")
                    break
                print("[WARNING] Failed to read frame.")
                time.sleep(0.05)
                continue

            t0 = time.perf_counter()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = preprocess(gray)
            corners, ids, _ = detector.detectMarkers(gray)

            detect_ms = (time.perf_counter() - t0) * 1000.0
            ts  = now_ms()
            now = time.time()

            vis            = frame.copy()
            detected_info  = []
            kept_corners   = []
            kept_ids       = []

            found = []
            corner_of = {}
            raw_corners = []
            if ids is not None and len(corners) > 0:
                for corner, marker_id in zip(corners, ids.flatten()):
                    if marker_min_side(corner) < MIN_SIDE_PX:
                        continue
                    found.append((int(marker_id), *center_of(corner)))
                    corner_of.setdefault(int(marker_id), []).append(corner)
                    raw_corners.append(corner)

            if tracker is not None:
                found = tracker.update(found)

            for marker_id, cx, cy in found:
                # Draw the raw outline nearest the reported position
                corner = min(corner_of[marker_id], key=lambda c: cv2.norm(c[0].mean(axis=0) - (cx, cy)))
                kept_corners.append(corner)
                kept_ids.append(marker_id)

                label = ARUCO_LABELS.get(marker_id, f"unknown_{marker_id}")
                detected_info.append((marker_id, label, cx, cy))

                last_ts = last_written.get(marker_id, 0)
                if ts - last_ts >= WRITE_COOLDOWN_MS:
                    writer.writerow([ts, marker_id, label, cx, cy])
                    csv_file.flush()
                    last_written[marker_id] = ts

            rejected = [c for c in raw_corners if not any(c is k for k in kept_corners)]
            if rejected:
                cv2.aruco.drawDetectedMarkers(vis, rejected, borderColor=REJECTED_COLOR)
            if kept_ids:
                cv2.aruco.drawDetectedMarkers(vis, kept_corners, np.array(kept_ids).reshape(-1, 1))

            tick = time.perf_counter()
            if last_tick is not None:
                # Frames processed per second, smoothed so the number is readable
                dt  = max(tick - last_tick, 1e-6)
                fps = 0.9 * fps + 0.1 / dt if fps else 1 / dt
            last_tick = tick
            draw_status(vis, detect_ms, fps, len(kept_corners), len(rejected))

            if args.record:
                if recorder is None:
                    height, width = vis.shape[:2]
                    recorder = cv2.VideoWriter(args.record, cv2.VideoWriter_fourcc(*RECORD_CODEC),
                                               RECORD_FPS, (width, height))
                recorder.write(vis)

            if args.show:
                cv2.imshow(SHOW_WINDOW, vis)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\n[INFO] Stopping...")
                    break

            # Terminal log
            if now - last_log >= LOG_EVERY_SEC:
                last_log = now
                print_detections(detect_ms, detected_info)

            #  Save debug image 
            if now - last_save >= SAVE_EVERY_SEC:
                last_save = now
                cv2.imwrite(DEBUG_IMAGE_PATH, vis)

            last_frame = (detect_ms, detected_info, vis)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping...")

    finally:
        camera.release()
        csv_file.close()
        if recorder is not None:
            recorder.release()
            print(f"[INFO] Video saved to {args.record}")
        if args.show:
            cv2.destroyAllWindows()
        print(f"[INFO] Camera released. Detections saved to {DETECTION_LOG}")


if __name__ == "__main__":
    main()