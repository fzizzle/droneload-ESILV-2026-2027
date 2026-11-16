from droneload.vision.tracking.tracker import MarkerTracker

SIDE = 60  # gate max(20, 45) = 45 px, so the 30 px/frame and 200 px cases keep their meaning

def run(frames):
    tracker = MarkerTracker()
    return [tracker.update([d if len(d) == 4 else (*d, SIDE) for d in frame]) for frame in frames]

def test_confirms_after_three_frames():
    out = run([[(4, 100, 100)]] * 3)
    assert out[0] == [] and out[1] == []
    assert [m[0] for m in out[2]] == [4]

def test_single_frame_flicker_never_reported():
    out = run([[(7, 100, 100)]] + [[]] * 4)
    assert all(o == [] for o in out)

def test_reports_detected_position():
    out = run([[(1, 0, 0)]] * 3 + [[(1, 10, 0)]])
    assert out[-1] == [(1, 10.0, 0.0)]

def test_jump_restarts_confirmation():
    out = run([[(1, 0, 0)]] * 3 + [[(1, 200, 0)]])
    assert out[-1] == []

def test_brief_gap_keeps_track():
    hit = [(2, 50, 50)]
    out = run([hit, hit, hit, [], hit])
    assert [m[0] for m in out[-1]] == [2]

def test_expires_after_window():
    hit = [(2, 50, 50)]
    out = run([hit] * 3 + [[]] * 5 + [hit])
    assert out[-1] == []

def test_duplicate_id_follows_nearest():
    out = run([[(3, 100, 100)]] * 3 + [[(3, 400, 400), (3, 102, 100)]])
    assert len(out[-1]) == 1
    marker_id, cx, cy = out[-1][0]
    assert marker_id == 3 and cx == 102 and cy == 100

def test_follows_steady_motion():
    out = run([[(5, 20 * i, 0)] for i in range(10)])
    assert all([m[0] for m in o] == [5] for o in out[2:])

def test_output_sorted_by_id():
    out = run([[(9, 0, 0), (0, 300, 300)]] * 3)
    assert [m[0] for m in out[-1]] == [0, 9]

def test_false_positive_does_not_break_confirmed_track():
    out = run([[(3, 100, 100)]] * 3 + [[(3, 400, 400)], [(3, 100, 100)]])
    assert out[-2] == []
    assert [m[0] for m in out[-1]] == [3]

def test_follows_fast_motion():
    out = run([[(5, 30 * i, 0)] for i in range(10)])
    assert all([m[0] for m in o] == [5] for o in out[2:])

def test_one_miss_while_moving_keeps_track():
    frames = [[(5, 20 * i, 0)] for i in range(10)]
    frames[5] = []
    out = run(frames)
    assert [m[0] for m in out[6]] == [5]

def test_gate_scales_with_marker_side():
    big = run([[(5, 100 * i, 0, 200)] for i in range(6)])      # gate 150 px
    assert all([m[0] for m in o] == [5] for o in big[2:])
    small = run([[(5, 0, 0, 40)]] * 3 + [[(5, 100, 0, 40)]])  # gate 30 px
    assert small[-1] == []

def test_gate_has_pixel_floor():
    out = run([[(5, 15 * i, 0, 10)] for i in range(6)])       # 0.75 x 10 < 20 px floor
    assert all([m[0] for m in o] == [5] for o in out[2:])

def test_gate_uses_track_side():
    out = run([[(3, 100, 100, 40)]] * 3 + [[(3, 300, 100, 400)]])
    assert out[-1] == []

def test_smoothing_weight_is_configurable():
    tracker = MarkerTracker(smoothing=0.6)
    out = [tracker.update([(1, x, 0, SIDE)]) for x in (0, 0, 0, 10)]
    assert out[-1] == [(1, 6.0, 0.0)]
