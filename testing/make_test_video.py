# Write a short video of moving ArUco markers, for running the detector without a camera:
#   python3 -m testing.make_test_video
#   python3 -m droneload.vision --source test_markers.mp4
import cv2
import numpy as np

OUTPUT     = "test_markers.mp4"
SIZE       = (1280, 720)
FPS        = 30
NUM_FRAMES = 150
MARKER_IDS = [0, 1, 4]
MARKER_PX  = 150

def main():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    w, h       = SIZE
    writer     = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), FPS, SIZE)

    for i in range(NUM_FRAMES):
        t     = i / NUM_FRAMES
        frame = np.full((h, w), 200, np.uint8)

        for n, marker_id in enumerate(MARKER_IDS):
            marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, MARKER_PX)
            x = 150 + n * 350 + int(100 * t)
            y = 250 + int(100 * np.sin(2 * np.pi * t + n))
            frame[y:y + MARKER_PX, x:x + MARKER_PX] = marker

        # Drone-like tilt, motion blur and fading light
        rotation = cv2.getRotationMatrix2D((w / 2, h / 2), 15 * np.sin(2 * np.pi * t), 1.0)
        frame    = cv2.warpAffine(frame, rotation, SIZE, borderValue=200)
        frame    = cv2.GaussianBlur(frame, (5, 5), 0)
        frame    = cv2.convertScaleAbs(frame, alpha=1.0 - 0.7 * t)

        writer.write(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR))

    writer.release()
    print(f"[INFO] Wrote {NUM_FRAMES} frames to {OUTPUT}")

if __name__ == "__main__":
    main()
