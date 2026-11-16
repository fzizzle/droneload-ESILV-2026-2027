import math

import pytest

from analysis.smoothing import study
from testing import vibration_test

SIDE = 60

def synthetic(detections, truth=None, real=frozenset({1})):
    """Return a Run and a Detected for synthetic (id, x, y, side) frames."""
    if truth is None:
        truth = [{m: (float(x), float(y)) for m, x, y, _ in frame if m in real} for frame in detections]
    run = study.Run("moderate", 1, detections, truth, truth)
    return run, study.Detected("synthetic", set(real), [set(t) for t in truth], [run])

def moving(xs):
    return [[(1, x, 0, SIDE)] for x in xs]

def test_replay_full_weight_reports_detections():
    d = moving([0, 10, 20, 30])
    assert study.replay(d, 1.0)[3] == {1: (30.0, 0.0)}
    assert study.replay(d, 0.5)[3][1][0] < 30
    assert study.replay(d, None)[0] == {1: (0.0, 0.0)}

def test_recall_does_not_depend_on_weight():
    xs = [15 * i for i in range(20)]
    truth = [{1: (float(x), 0.0)} for x in xs]
    detections = [[] if i in (4, 8, 9) else [(1, x, 0, SIDE)] for i, x in enumerate(xs)]
    for i in range(10, 15):
        detections[i] = detections[i] + [(9, 500, 500, SIDE)]
    run, detected = synthetic(detections, truth)
    low  = study.measure(run, study.replay(detections, 0.1), detected)
    full = study.measure(run, study.replay(detections, 1.0), detected)
    assert low["tracked"] == full["tracked"] > 0
    assert low["false_ids"] == full["false_ids"] > 0
    assert low["frame_err_px"] > full["frame_err_px"]

def test_measure_reports_equal_truth():
    run, detected = synthetic(moving([0, 5, 15, 30, 50]))
    m = study.measure(run, run.truth, detected)
    assert m["frame_err_px"] == 0 and m["steady_err_px"] == 0
    assert m["jitter_px"] == m["true_jitter_px"] > 0
    assert m["tracked"] == 1.0 and m["false_ids"] == 0

def test_measure_no_reports_is_nan():
    run, detected = synthetic(moving([0, 5, 15]))
    m = study.measure(run, [{}] * 3, detected)
    for key in ("frame_err_px", "steady_err_px", "jitter_px", "true_jitter_px"):
        assert math.isnan(m[key])
    assert m["tracked"] == 0 and m["false_ids"] == 0

def test_steady_matrix():
    centre = vibration_test.map_point(study.steady_matrix(100, 100, 1.5), 50, 50)
    assert centre == pytest.approx((50, 50))
    corner = vibration_test.map_point(study.steady_matrix(100, 100, 2.0), 0, 0)
    assert corner == pytest.approx((-50, -50))

def row(seed, frame_err, weight=0.5, level="mild"):
    r = dict(footage="f", level=level, seed=seed, weight=weight)
    r.update({key: 0.0 for key in study.METRICS})
    r["frame_err_px"] = frame_err
    return r

def test_summarise_mean_min_max():
    out = study.summarise([row(1, 1.0), row(2, 3.0), row(3, math.nan)])
    assert len(out) == 1
    s = out[0]
    assert (s["footage"], s["level"], s["weight"]) == ("f", "mild", 0.5)
    assert (s["frame_err_px_mean"], s["frame_err_px_min"], s["frame_err_px_max"]) == (2.0, 1.0, 3.0)

def test_summarise_orders_levels_and_raw_first():
    rows = [row(1, 1.0, 1.0, "moderate"), row(1, 1.0, None, "moderate"), row(1, 1.0, 0.2, "clean")]
    out = study.summarise(rows)
    assert [(s["level"], s["weight"]) for s in out] == [("clean", 0.2), ("moderate", None), ("moderate", 1.0)]

def test_detect_runs_generated():
    frames = [vibration_test.make_frame(240)] * 15
    detected = study.detect_runs(frames, "DICT_4X4_50", seeds=(1, 2), footage="generated")
    assert detected.real == {0}
    assert len(detected.runs) == 1 + 3 * 2
    assert detected.runs[0].level == "clean"
    assert detected.runs[0].truth[0][0] == pytest.approx(detected.runs[0].steady[0][0])
    assert study.busiest_marker(detected) == 0

def test_cache_path_includes_seeds():
    assert study.cache_path("x", (1, 2)) != study.cache_path("x", (1,))

def test_missing_footage_names_readme(monkeypatch, tmp_path):
    monkeypatch.setattr(study, "FOOTAGE", {"x": ("missing/none.mp4", "DICT_4X4_50")})
    monkeypatch.setattr(study, "OUTPUT_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="Test Footage"):
        study.load_or_detect("x")

def test_trace_has_gaps_where_not_reported():
    run, detected = synthetic(moving([0, 10, 20, 30]))
    t = study.trace(detected, level="moderate", seed=1, weights=(1.0,))
    assert t["marker_id"] == 1 and t["frames"] == [0, 1, 2, 3]
    assert t["truth_x"] == [0.0, 10.0, 20.0, 30.0]
    assert t["weights"][1.0] == [None, None, 20.0, 30.0]

def test_format_table_shows_raw_and_percent():
    text = study.format_table(study.summarise([row(1, 1.0, None), row(1, 1.0, 0.5)]))
    assert "raw" in text and "0.5" in text and "%" in text
