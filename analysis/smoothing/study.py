# How the tracker's smoothing weight changes position error and jitter under shake.
# Detection runs once per footage, shake level and seed; the cached detections are
# then replayed through one tracker per weight, because smoothing does not change
# what is detected. See smoothing_study.ipynb for the walkthrough.
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import math
import pickle

import cv2
import numpy as np

from droneload.vision import detect
from droneload.vision.tracking.tracker import SMOOTHING, MarkerTracker
from testing import vibration_test
from testing.vibration_test import SHAKE_LEVELS, first_by_id, map_point

WEIGHTS    = [round(0.1 * i, 1) for i in range(1, 11)]  # 1.0 means no smoothing
SEEDS      = (1, 2, 3)                                  # shake paths; seed 1 is the logged baseline
FOOTAGE    = {
    "fdcl-gwu":     ("test_footage/fdcl-gwu/test_video.mp4", "DICT_ARUCO_ORIGINAL"),
    "shadow-aruco": ("test_footage/shadow-aruco/video_5/%05d.png", "DICT_ARUCO_MIP_36h12"),
}
ROOT       = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).parent / "output"
CACHE_VERSION = 2  # bump when Run or Detected changes, so old caches are not read
METRICS    = ("frame_err_px", "steady_err_px", "jitter_px", "true_jitter_px", "tracked", "false_ids")

@dataclass
class Run:
    """One shaken pass over the footage."""
    level: str
    seed: int
    detections: list  # find_markers output per frame
    truth: list       # {id: [(x, y), ...]} per frame: where each real marker is in the shaken frame
    steady: list      # {id: [(x, y), ...]} per frame: where it would be with the camera held still
    # Lists, because a frame can hold two markers with the same ID

@dataclass
class Detected:
    footage: str
    real: set         # IDs the tracker confirms in enough clean frames
    reference: list   # real IDs the detector finds in each clean frame
    runs: list

def steady_matrix(width, height, zoom):
    """The shake transform with sway, jitter and rotation removed: zoom only."""
    return cv2.getRotationMatrix2D((width / 2, height / 2), 0, zoom)

def _detect_pass(frames, level, seed, detector):
    detections, matrices = [], []
    for shaken, _, matrix in vibration_test.shaken_frames(frames, level, seed):
        detections.append(vibration_test.find_markers(shaken, detector))
        matrices.append(matrix)
    return detections, matrices

def replay(detections, smoothing):
    """Return {id: (cx, cy)} per frame from a fresh tracker; None gives the raw detections."""
    if smoothing is None:
        return [first_by_id(frame) for frame in detections]
    tracker = MarkerTracker(smoothing)
    return [first_by_id(tracker.update(frame)) for frame in detections]

def detect_runs(frames, dict_name, seeds=SEEDS, footage=""):
    """Detect markers in the footage at every shake level and seed."""
    detector  = detect.make_detector(dict_name)
    height, width = frames[0].shape[:2]
    clean_detections, _ = _detect_pass(frames, SHAKE_LEVELS["clean"], seeds[0], detector)
    clean_raw = replay(clean_detections, None)
    counts    = Counter(marker_id for ids in replay(clean_detections, SMOOTHING) for marker_id in ids)
    real      = {marker_id for marker_id, count in counts.items() if count >= vibration_test.REAL_MIN_FRAMES}
    reference = [ids.keys() & real for ids in clean_raw]
    clean_all = [{} for _ in clean_detections]
    for positions, frame in zip(clean_all, clean_detections):
        for marker_id, cx, cy, _ in frame:
            if marker_id in real:
                positions.setdefault(marker_id, []).append((cx, cy))

    runs = []
    for name, level in SHAKE_LEVELS.items():
        steady = steady_matrix(width, height, level["zoom"])
        for seed in seeds[:1] if name == "clean" else seeds:
            if name == "clean":
                detections, matrices = clean_detections, [steady] * len(frames)
            else:
                detections, matrices = _detect_pass(frames, level, seed, detector)
            truth = [{m: [map_point(matrix, *p) for p in points] for m, points in positions.items()}
                     for positions, matrix in zip(clean_all, matrices)]
            still = [{m: [map_point(steady, *p) for p in points] for m, points in positions.items()}
                     for positions in clean_all]
            runs.append(Run(name, seed, detections, truth, still))
    return Detected(footage, real, reference, runs)

def cache_path(footage, seeds):
    return OUTPUT_DIR / f"{footage}-v{CACHE_VERSION}-seeds-{'-'.join(map(str, seeds))}.pkl"

def load_or_detect(footage, seeds=SEEDS, refresh=False):
    """Return the footage's detections, from the cache when it exists."""
    path = cache_path(footage, seeds)
    if path.exists() and not refresh:
        with open(path, "rb") as f:
            return pickle.load(f)
    source, dict_name = FOOTAGE[footage]
    frames, _ = vibration_test.read_frames(str(ROOT / source))
    if not frames:
        raise FileNotFoundError(f"No frames in {ROOT / source}. Download it as the README's "
                                f"\"Test Footage\" section shows.")
    detected = detect_runs(frames, dict_name, seeds, footage)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(detected, f)
    return detected

def _mean(values):
    return float(np.mean(values)) if values else math.nan

def _rms(values):
    return float(np.sqrt(np.mean(np.square(values)))) if values else math.nan

def measure(run, reported, detected):
    """Score one replay of a run against where the markers really are.

    Each report is matched to the nearest true copy of its ID."""
    frame_err, steady_err, steps, true_steps = [], [], [], []
    matched = [{} for _ in reported]  # the true point each report was matched to
    for t, positions in enumerate(reported):
        for m, point in positions.items():
            if m not in run.truth[t]:
                continue
            i = min(range(len(run.truth[t][m])), key=lambda i: math.dist(point, run.truth[t][m][i]))
            matched[t][m] = run.truth[t][m][i]
            frame_err.append(math.dist(point, matched[t][m]))
            steady_err.append(math.dist(point, run.steady[t][m][i]))
            if t and m in matched[t - 1]:
                steps.append(math.dist(point, reported[t - 1][m]))
                true_steps.append(math.dist(matched[t][m], matched[t - 1][m]))
    total = sum(len(ids) for ids in detected.reference)
    return dict(
        frame_err_px   = _mean(frame_err),
        steady_err_px  = _mean(steady_err),
        jitter_px      = _rms(steps),
        true_jitter_px = _rms(true_steps),
        tracked        = sum(len(r & s.keys()) for r, s in zip(detected.reference, reported)) / total,
        false_ids      = 100 * sum(len(s.keys() - detected.real) for s in reported) / len(reported),
    )

def sweep(detected, weights=WEIGHTS):
    """Return one row per run and weight, plus weight None for the raw detections."""
    rows = []
    for run in detected.runs:
        for weight in [None, *weights]:
            row = dict(footage=detected.footage, level=run.level, seed=run.seed, weight=weight)
            row.update(measure(run, replay(run.detections, weight), detected))
            rows.append(row)
    return rows

def summarise(rows):
    """Return the mean, min and max of each measure per footage, level and weight, ignoring nan."""
    groups = {}
    for row in rows:
        groups.setdefault((row["footage"], row["level"], row["weight"]), []).append(row)
    levels = list(SHAKE_LEVELS)
    keys = sorted(groups, key=lambda k: (k[0], levels.index(k[1]), -1 if k[2] is None else k[2]))
    out = []
    for footage, level, weight in keys:
        summary = dict(footage=footage, level=level, weight=weight)
        for metric in METRICS:
            values = [r[metric] for r in groups[footage, level, weight] if not math.isnan(r[metric])]
            summary[f"{metric}_mean"] = _mean(values)
            summary[f"{metric}_min"]  = min(values) if values else math.nan
            summary[f"{metric}_max"]  = max(values) if values else math.nan
        out.append(summary)
    return out

def busiest_marker(detected):
    """Return the real ID the clean detector finds in the most frames."""
    return Counter(m for ids in detected.reference for m in ids).most_common(1)[0][0]

def trace(detected, level="moderate", seed=SEEDS[0], weights=(0.6, 1.0), marker_id=None):
    """Return one marker's x position per frame: truth, raw and each weight, None where absent."""
    run = next(r for r in detected.runs if r.level == level and r.seed == seed)
    marker_id = busiest_marker(detected) if marker_id is None else marker_id

    def xs(positions):
        return [p[marker_id][0] if marker_id in p else None for p in positions]

    truth_x, last = [], None  # with two copies of the ID, follow the one nearest the last point
    for positions in run.truth:
        points = positions.get(marker_id)
        if not points:
            truth_x.append(None)
            continue
        last = points[0] if last is None else min(points, key=lambda p: math.dist(p, last))
        truth_x.append(last[0])

    return dict(
        marker_id = marker_id,
        frames    = list(range(len(run.truth))),
        truth_x   = truth_x,
        raw_x     = xs(replay(run.detections, None)),
        weights   = {w: xs(replay(run.detections, w)) for w in weights},
    )

def format_table(summary, metrics=("tracked", "false_ids")):
    """Return the summary as a plain text table, one line per level and weight."""
    def cell(metric, value):
        if math.isnan(value):
            return "-"
        return f"{100 * value:.1f}%" if metric == "tracked" else f"{value:.1f}"

    lines = [f"{'footage':<14}{'level':<10}{'weight':>7}" + "".join(f"{m:>16}" for m in metrics)]
    for s in summary:
        weight = "raw" if s["weight"] is None else f"{s['weight']:.1f}"
        lines.append(f"{s['footage']:<14}{s['level']:<10}{weight:>7}"
                     + "".join(f"{cell(m, s[m + '_mean']):>16}" for m in metrics))
    return "\n".join(lines)
