# Measure how simulated vibration affects marker detection, in a short table:
#   python -m testing.vibration_test
# Or shake real footage, as a poorly stabilised camera would, and compare with the clean footage:
#   python -m testing.vibration_test --source FOOTAGE --dict DICTIONARY
import argparse
import math

import cv2
import numpy as np

from droneload.vision import detect
from droneload.vision.tracking.tracker import MarkerTracker

SIZE            = (1280, 720)
MARKER_ID       = 0
MARKER_SIDES_PX = [60, 120, 240]
BLUR_PX         = [0, 5, 10, 20, 30, 40]
WOBBLE_PX       = [0, 5, 10, 20, 40]
WOBBLE_PERIOD   = 100
TRIALS          = 12

# Shake amplitudes in px for an 800 px wide frame, scaled to the footage width:
# drift is slow sway, jitter is frame-to-frame shake, rot is in degrees,
# wobble is rolling shutter, and zoom crops the black borders the shake leaves
SHAKE_LEVELS = {
    "clean":    dict(drift=0,  jitter=0,  rot=0.0, wobble=0, zoom=1.00),
    "mild":     dict(drift=10, jitter=3,  rot=1.0, wobble=0, zoom=1.06),
    "moderate": dict(drift=25, jitter=10, rot=3.0, wobble=2, zoom=1.12),
    "severe":   dict(drift=40, jitter=25, rot=6.0, wobble=5, zoom=1.20),
}
SHAKE_WIDTH_PX  = 800
EXPOSURE        = 0.5  # share of the frame interval the shutter is open; sets blur length
REAL_MIN_FRAMES = 10   # a marker is real if the tracker confirms it in this many clean frames
SEED            = 1

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

def find_markers(frame, detector):
    """Return (id, cx, cy) for each marker, filtered as the detection loop does."""
    gray = detect.preprocess(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    corners, ids, _ = detector.detectMarkers(gray)
    if ids is None:
        return []
    return [(int(marker_id), *detect.center_of(corner)) for corner, marker_id in zip(corners, ids.flatten())
            if detect.marker_min_side(corner) >= detect.MIN_SIDE_PX]

def is_found(frame, detector):
    return any(marker_id == MARKER_ID for marker_id, _, _ in find_markers(frame, detector))

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

def read_frames(source):
    capture, frames = cv2.VideoCapture(source), []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    return frames

def shake_path(count, level, scale):
    """Return (dx, dy, angle) per frame: slow random sway plus fast jitter."""
    rng  = np.random.default_rng(SEED)
    t    = np.arange(count)
    path = np.zeros((count, 3))
    for axis, amplitude in enumerate([level["drift"] * scale, level["drift"] * scale, level["rot"]]):
        for _ in range(3):  # sines with random periods of 1-4 s at 30 fps
            period, phase = rng.uniform(30, 120), rng.uniform(0, 2 * np.pi)
            path[:, axis] += amplitude / 3 * np.sin(2 * np.pi * t / period + phase)
    path[:, :2] += rng.normal(0, level["jitter"] * scale, (count, 2))
    path[:, 2]  += rng.normal(0, level["rot"] / 3, count)
    return path

def shake_frame(frame, pose, previous_pose, level, scale, index):
    """Move the frame to pose, blurred along the move since the previous frame."""
    height, width = frame.shape[:2]
    dx, dy, angle = pose
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, level["zoom"])
    matrix[:, 2] += (dx, dy)
    shaken = cv2.warpAffine(frame, matrix, (width, height))
    move_x, move_y = np.subtract(pose[:2], previous_pose[:2])
    blur_px = int(EXPOSURE * math.hypot(move_x, move_y))
    if blur_px >= 2:
        shaken = motion_blur(shaken, blur_px, math.degrees(math.atan2(move_y, move_x)))
    if level["wobble"]:
        shaken = rolling_wobble(shaken, level["wobble"] * scale, index * 1.7)
    return shaken, math.hypot(move_x, move_y)

def shake_run(frames, level, detector):
    """Return per-frame raw IDs, tracked IDs and movement in px."""
    scale   = frames[0].shape[1] / SHAKE_WIDTH_PX
    path    = shake_path(len(frames), level, scale)
    tracker = MarkerTracker()
    raw, tracked, moves = [], [], []
    for index, frame in enumerate(frames):
        shaken, move = shake_frame(frame, path[index], path[max(index - 1, 0)], level, scale, index)
        found = find_markers(shaken, detector)
        raw.append({marker_id for marker_id, _, _ in found})
        tracked.append({marker_id for marker_id, _, _ in tracker.update(found)})
        moves.append(move)
    return raw, tracked, moves

def shake_rates(frames, detector):
    """Return the real marker IDs and, per level, the share of clean detections kept."""
    clean_raw, clean_tracked, _ = shake_run(frames, SHAKE_LEVELS["clean"], detector)
    counts = {}
    for ids in clean_tracked:
        for marker_id in ids:
            counts[marker_id] = counts.get(marker_id, 0) + 1
    real      = {marker_id for marker_id, count in counts.items() if count >= REAL_MIN_FRAMES}
    reference = [ids & real for ids in clean_raw]
    total     = sum(len(ids) for ids in reference)
    rates = {}
    for name, level in SHAKE_LEVELS.items():
        raw, tracked, moves = shake_run(frames, level, detector)
        rates[name] = dict(
            move_px     = float(np.mean(moves)),
            move_p95_px = float(np.percentile(moves, 95)),
            raw         = sum(len(r & s) for r, s in zip(reference, raw)) / total,
            tracked     = sum(len(r & s) for r, s in zip(reference, tracked)) / total,
            false_ids   = 100 * sum(len(s - real) for s in tracked) / len(frames),
        )
    return real, rates

def print_shake_table(frames, detector):
    real, rates = shake_rates(frames, detector)
    print(f"{len(frames)} frames, real markers {sorted(real)}")
    print(f"{'level':<10}{'move px':>9}{'p95':>6}{'raw':>8}{'tracked':>9}{'false IDs/100 frames':>22}")
    for name, rate in rates.items():
        print(f"{name:<10}{rate['move_px']:>9.1f}{rate['move_p95_px']:>6.0f}{100 * rate['raw']:>7.1f}%"
              f"{100 * rate['tracked']:>8.1f}%{rate['false_ids']:>22.1f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="footage to shake; without it, a generated marker is used")
    parser.add_argument("--dict", default=detect.ARUCO_DICT, help="cv2.aruco dictionary name")
    args = parser.parse_args()

    detector = detect.make_detector(args.dict)
    if args.source:
        print_shake_table(read_frames(args.source), detector)
        return
    print_table("blur px", BLUR_PX, lambda frame, level: blur_rate(frame, level, detector))
    print_table("wobble px", WOBBLE_PX, lambda frame, level: wobble_rate(frame, level, detector))

if __name__ == "__main__":
    main()
