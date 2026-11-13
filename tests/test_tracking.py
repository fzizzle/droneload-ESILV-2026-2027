from droneload.vision.tracking.tracker import MarkerTracker

def run(frames):
    tracker = MarkerTracker()
    return [tracker.update(frame) for frame in frames]

def test_confirms_after_three_frames():
    out = run([[(4, 100, 100)]] * 3)
    assert out[0] == [] and out[1] == []
    assert [m[0] for m in out[2]] == [4]

def test_single_frame_flicker_never_reported():
    out = run([[(7, 100, 100)]] + [[]] * 4)
    assert all(o == [] for o in out)

def test_smooths_position():
    out = run([[(1, 0, 0)]] * 3 + [[(1, 10, 0)]])
    assert out[-1] == [(1, 6.0, 0.0)]

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
    assert marker_id == 3 and 100 < cx < 102 and cy == 100

def test_follows_steady_motion():
    out = run([[(5, 20 * i, 0)] for i in range(10)])
    assert all([m[0] for m in o] == [5] for o in out[2:])

def test_output_sorted_by_id():
    out = run([[(9, 0, 0), (0, 300, 300)]] * 3)
    assert [m[0] for m in out[-1]] == [0, 9]
