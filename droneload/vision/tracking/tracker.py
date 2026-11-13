# Confirms markers across frames and smooths their pixel positions.
from collections import deque
from dataclasses import dataclass, field
import math

# Tracking settings
CONFIRM_FRAMES = 3     # hits needed in the window before a marker is reported
WINDOW_FRAMES  = 5     # recent frames remembered per marker
MAX_JUMP_PX    = 40.0  # farthest move per frame from the last detection
SMOOTHING      = 0.6   # weight of the new position; 1.0 means no smoothing

@dataclass
class _Track:
    cx: float              # smoothed position, reported
    cy: float
    raw: tuple = None      # last detected position, used for the jump check
    since_hit: int = 1     # frames since the last detection
    hits: deque = field(default_factory=lambda: deque([True], maxlen=WINDOW_FRAMES))

    def __post_init__(self):
        self.raw = (self.cx, self.cy)

    def confirmed(self):
        return sum(self.hits) >= CONFIRM_FRAMES

class MarkerTracker:
    """Keeps one track per marker ID and reports only confirmed markers."""

    def __init__(self):
        self.tracks = {}

    def update(self, detections):
        """Take this frame's (id, cx, cy) list; return confirmed (id, cx, cy), sorted by ID."""
        by_id = {}
        for marker_id, cx, cy in detections:
            by_id.setdefault(int(marker_id), []).append((float(cx), float(cy)))

        seen = set()
        for marker_id, points in by_id.items():
            track = self.tracks.get(marker_id)
            if track is None:
                self.tracks[marker_id] = _Track(*points[0])
                seen.add(marker_id)
                continue
            cx, cy = min(points, key=lambda p: math.dist(p, track.raw))
            if math.dist((cx, cy), track.raw) <= MAX_JUMP_PX * track.since_hit:
                track.cx += SMOOTHING * (cx - track.cx)
                track.cy += SMOOTHING * (cy - track.cy)
                track.raw = (cx, cy)
                track.since_hit = 1
                track.hits.append(True)
                seen.add(marker_id)
            elif not track.confirmed():
                # A far detection replaces an unconfirmed track
                self.tracks[marker_id] = _Track(cx, cy)
                seen.add(marker_id)
            # A far detection is a miss for a confirmed track, so one false
            # positive cannot move it

        for marker_id, track in list(self.tracks.items()):
            if marker_id not in seen:
                track.hits.append(False)
                track.since_hit += 1
                if not any(track.hits):
                    del self.tracks[marker_id]

        return [(marker_id, round(track.cx, 1), round(track.cy, 1))
                for marker_id, track in sorted(self.tracks.items())
                if marker_id in seen and track.confirmed()]
