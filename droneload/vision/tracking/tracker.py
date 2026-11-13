# Confirms markers across frames and smooths their pixel positions.
from collections import deque
from dataclasses import dataclass, field
import math

# Tracking settings
CONFIRM_FRAMES = 3     # hits needed in the window before a marker is reported
WINDOW_FRAMES  = 5     # recent frames remembered per marker
MAX_JUMP_PX    = 40.0  # farther than this from the track starts a new track
SMOOTHING      = 0.6   # weight of the new position; 1.0 means no smoothing

@dataclass
class _Track:
    cx: float
    cy: float
    hits: deque = field(default_factory=lambda: deque([True], maxlen=WINDOW_FRAMES))

class MarkerTracker:
    """Keeps one track per marker ID and reports only confirmed markers."""

    def __init__(self):
        self.tracks = {}

    def update(self, detections):
        """Take this frame's (id, cx, cy) list; return confirmed (id, cx, cy), sorted by ID."""
        by_id = {}
        for marker_id, cx, cy in detections:
            by_id.setdefault(int(marker_id), []).append((float(cx), float(cy)))

        for marker_id, points in by_id.items():
            track = self.tracks.get(marker_id)
            if track is None:
                cx, cy = points[0]
            else:
                cx, cy = min(points, key=lambda p: math.dist(p, (track.cx, track.cy)))
            if track is None or math.dist((cx, cy), (track.cx, track.cy)) > MAX_JUMP_PX:
                self.tracks[marker_id] = _Track(cx, cy)
            else:
                track.cx += SMOOTHING * (cx - track.cx)
                track.cy += SMOOTHING * (cy - track.cy)
                track.hits.append(True)

        for marker_id, track in list(self.tracks.items()):
            if marker_id not in by_id:
                track.hits.append(False)
                if not any(track.hits):
                    del self.tracks[marker_id]

        return [(marker_id, round(track.cx, 1), round(track.cy, 1))
                for marker_id, track in sorted(self.tracks.items())
                if marker_id in by_id and sum(track.hits) >= CONFIRM_FRAMES]
