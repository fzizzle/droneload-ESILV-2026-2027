# Score detection against Shadow-ArUco ground truth, in one line of output:
#   python3 benchmark.py
import argparse
import glob
import json
import os

import cv2
import numpy as np

import main

MATCH_DISTANCE_PX = 15

def load_truth(image_path):
    folder, name = os.path.split(image_path)
    with open(os.path.join(folder, "corrected_annotations", name.replace(".png", ".json"))) as f:
        markers = json.load(f)["markers"]
    return {m["id"]: np.mean([[c["x"], c["y"]] for c in m["corners"]], axis=0) for m in markers}

def score(paths, detector):
    matched = unmatched = annotated = 0
    for path in paths:
        truth = load_truth(path)
        annotated += len(truth)
        gray = main.preprocess(cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY))
        corners, ids, _ = detector.detectMarkers(gray)
        for corner, marker_id in zip(corners, [] if ids is None else ids.flatten().tolist()):
            near = marker_id in truth and np.linalg.norm(corner[0].mean(axis=0) - truth[marker_id]) < MATCH_DISTANCE_PX
            matched   += near
            unmatched += not near
    return matched, unmatched, annotated

def main_benchmark():
    parser = argparse.ArgumentParser(description="Score detection against ground truth")
    parser.add_argument("--footage", default="../test_footage/shadow-aruco/video_5")
    parser.add_argument("--dict", default="DICT_ARUCO_MIP_36h12")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.footage, "*.png")))
    if not paths:
        print(f"[ERROR] No images in {args.footage}. See Test Footage in README.md.")
        exit(1)

    matched, unmatched, annotated = score(paths, main.make_detector(args.dict))
    detections = matched + unmatched
    print(f"frames={len(paths)} found={100 * matched / annotated:.1f}% "
          f"unmatched={100 * unmatched / max(detections, 1):.1f}%")

if __name__ == "__main__":
    main_benchmark()
