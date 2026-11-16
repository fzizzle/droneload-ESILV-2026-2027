# Score detection against Shadow-ArUco ground truth, in one line of output:
#   python3 -m testing.benchmark
import argparse
import glob
import json
import os

import cv2
import numpy as np

from droneload.vision import detect
from droneload.vision.tracking.tracker import MarkerTracker
from testing import vibration_test

MATCH_DISTANCE_PX = 15

def load_truth(image_path):
    folder, name = os.path.split(image_path)
    with open(os.path.join(folder, "corrected_annotations", name.replace(".png", ".json"))) as f:
        markers = json.load(f)["markers"]
    return {m["id"]: np.mean([[c["x"], c["y"]] for c in m["corners"]], axis=0) for m in markers}

def score(paths, detector, tracker=None):
    """Score each frame in order; with a tracker, score only what it confirms."""
    matched = unmatched = annotated = 0
    for path in paths:
        truth = load_truth(path)
        annotated += len(truth)
        found = vibration_test.find_markers(cv2.imread(path), detector)
        if tracker is not None:
            found = tracker.update(found)
        for marker_id, cx, cy, *_ in found:
            near = marker_id in truth and np.linalg.norm(np.subtract((cx, cy), truth[marker_id])) < MATCH_DISTANCE_PX
            matched   += near
            unmatched += not near
    return matched, unmatched, annotated

def main():
    parser = argparse.ArgumentParser(description="Score detection against ground truth")
    parser.add_argument("--footage", default="test_footage/shadow-aruco/video_5")
    parser.add_argument("--dict", default="DICT_ARUCO_MIP_36h12")
    parser.add_argument("--track", action="store_true", help="score only markers the tracker confirms")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.footage, "*.png")))
    if not paths:
        print(f"[ERROR] No images in {args.footage}. See Test Footage in README.md.")
        exit(1)

    matched, unmatched, annotated = score(paths, detect.make_detector(args.dict),
                                        MarkerTracker() if args.track else None)
    detections = matched + unmatched
    print(f"frames={len(paths)} found={100 * matched / annotated:.1f}% "
          f"unmatched={100 * unmatched / max(detections, 1):.1f}%")

if __name__ == "__main__":
    main()
