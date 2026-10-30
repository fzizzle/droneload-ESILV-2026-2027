import os
import cv2

class OpenCVCamera:
    """Anything cv2.VideoCapture can open: device index, video file,
    image sequence (frames/%03d.jpg), stream URL or GStreamer pipeline."""

    def __init__(self, source="0", size=(1280, 720), fps=30):
        self.source = int(source) if str(source).isdigit() else source
        self.size   = size
        self.fps    = fps
        self.cap    = None
        # Files end; live sources should keep retrying
        self.finite = isinstance(self.source, str) and (
            os.path.isfile(self.source) or "%" in self.source
        )

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print(f"[ERROR] Failed to open source: {self.source}")
            return False
        if not self.finite:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.size[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        return True

    def read(self):
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
