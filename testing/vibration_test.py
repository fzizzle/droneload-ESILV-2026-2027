# Measure how simulated vibration affects marker detection, in a short table:
#   python -m testing.vibration_test
import cv2
import numpy as np

from droneload.vision import detect

SIZE            = (1280, 720)
MARKER_ID       = 0
MARKER_SIDES_PX = [60, 120, 240]
BLUR_PX         = [0, 5, 10, 20, 30, 40]
WOBBLE_PX       = [0, 5, 10, 20, 40]
WOBBLE_PERIOD   = 100
TRIALS          = 12

def make_frame(side_px):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    width, height = SIZE
    frame = np.full((height, width), 200, np.uint8)
    x, y  = (width - side_px) // 2, (height - side_px) // 2
    frame[y:y + side_px, x:x + side_px] = cv2.aruco.generateImageMarker(aruco_dict, MARKER_ID, side_px)
    return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

def motion_blur(frame, length_px, angle_deg):
    """Smear the image along a line, as camera movement during exposure does."""
    if length_px == 0:
        return frame
    kernel = np.zeros((length_px, length_px), np.float32)
    middle = length_px // 2
    kernel[middle, :] = 1
    rotation = cv2.getRotationMatrix2D((middle, middle), angle_deg, 1.0)
    kernel   = cv2.warpAffine(kernel, rotation, (length_px, length_px))
    return cv2.filter2D(frame, -1, kernel / kernel.sum())

def rolling_wobble(frame, amplitude_px, phase):
    """Shift each row sideways, as a rolling shutter does under vibration."""
    height, width = frame.shape[:2]
    map_x, map_y  = np.meshgrid(np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32))
    map_x += amplitude_px * np.sin(2 * np.pi * map_y / WOBBLE_PERIOD + phase)
    return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)

def is_found(frame, detector):
    gray = detect.preprocess(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    _, ids, _ = detector.detectMarkers(gray)
    return ids is not None and MARKER_ID in ids.flatten()

def blur_rate(frame, length_px, detector):
    angles = np.linspace(0, 180, TRIALS, endpoint=False)
    return np.mean([is_found(motion_blur(frame, length_px, a), detector) for a in angles])

def wobble_rate(frame, amplitude_px, detector):
    phases = np.linspace(0, 2 * np.pi, TRIALS, endpoint=False)
    return np.mean([is_found(rolling_wobble(frame, amplitude_px, p), detector) for p in phases])

def print_table(name, levels, rate):
    print(f"{name:<12}" + "".join(f"{level:>6}" for level in levels))
    for side in MARKER_SIDES_PX:
        frame = make_frame(side)
        print(f"{side:>7} px  " + "".join(f"{100 * rate(frame, level):>5.0f}%" for level in levels))

def main():
    detector = detect.make_detector()
    print_table("blur px", BLUR_PX, lambda frame, level: blur_rate(frame, level, detector))
    print_table("wobble px", WOBBLE_PX, lambda frame, level: wobble_rate(frame, level, detector))

if __name__ == "__main__":
    main()
