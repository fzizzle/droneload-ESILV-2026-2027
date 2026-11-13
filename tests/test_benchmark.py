import json

import cv2
import numpy as np

from droneload.vision import detect
from droneload.vision.tracking.tracker import MarkerTracker
from testing import benchmark

MARKER_PX = 150
PLACES = {0: (50, 50), 1: (350, 200)}

def write_frames(folder):
    """Five frames: marker 0 in all of them, marker 1 only in frame 3."""
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    (folder / "corrected_annotations").mkdir()
    paths = []
    for frame in range(1, 6):
        image = np.full((480, 640, 3), 255, np.uint8)
        markers = []
        for marker_id, (x, y) in PLACES.items():
            if marker_id == 1 and frame != 3:
                continue
            marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, MARKER_PX)
            image[y:y + MARKER_PX, x:x + MARKER_PX] = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
            corners = [(x, y), (x + MARKER_PX, y), (x + MARKER_PX, y + MARKER_PX), (x, y + MARKER_PX)]
            markers.append({"id": marker_id, "corners": [{"x": cx, "y": cy} for cx, cy in corners]})
        path = folder / f"{frame:05d}.png"
        cv2.imwrite(str(path), image)
        (folder / "corrected_annotations" / f"{frame:05d}.json").write_text(json.dumps({"markers": markers}))
        paths.append(str(path))
    return paths

def test_score_with_tracker_drops_flicker(tmp_path):
    paths = write_frames(tmp_path)
    detector = detect.make_detector("DICT_4X4_50")

    assert benchmark.score(paths, detector)[:2] == (6, 0)
    assert benchmark.score(paths, detector, MarkerTracker())[:2] == (3, 0)
