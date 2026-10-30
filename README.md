# Droneload: Real-Time ArUco Marker Detection

**English** | [Français](README.fr.md)

Detects ArUco markers from a camera or recorded footage, labels them, and logs their positions in the image. It was written for the RubikPi 3 (Qualcomm QCS6490), but runs on any machine with OpenCV.

The output is the pixel centre of each marker. It does not estimate pose or distance, and it sends nothing to a flight controller.

## Status

| Part | State |
|------|-------|
| Detection, labels and logging | Tested on a PC with generated and real footage |
| RubikPi CSI camera | Not tested on a board; the pipeline may need changing |
| Hardware | Not chosen yet |
| Project markers (`DICT_4X4_50`) | Not tested on real footage |

On the Shadow-ArUco test footage, the detector found 56% of annotated markers, and 27% of its detections did not match the annotations. That footage uses a different dictionary, so these figures may not apply to project markers. `Detect Aruco Realtime/TODO.md` tracks open work.

## Quick Start

Requires Python 3 and a PC. Run all commands from `Detect Aruco Realtime/`.

```bash
pip install opencv-contrib-python
python3 make_test_video.py                  # no camera needed
python3 main.py --source test_markers.mp4
```

Results go to `detections.csv` and `aruco_debug.jpg`.

## Usage

```bash
python3 main.py [--source SOURCE] [--dict DICTIONARY]
```

`--source` defaults to `0`, the first webcam. It accepts:

| Value | Source |
|-------|--------|
| `0`, `1`, ... | Webcam or other camera device |
| `video.mp4` | Video file |
| `"frames/%03d.jpg"` | Image sequence |
| GStreamer pipeline | Needs OpenCV built with GStreamer |
| `rubikpi-csi` | RubikPi CSI camera |
| `picamera` | Raspberry Pi camera, needs `picamera2` |

`--dict` takes a `cv2.aruco` dictionary name and defaults to `DICT_4X4_50`.

Video and image sources stop at the last frame. Press Ctrl+C to stop a live source.

## How It Works

1. Reads a frame from the source.
2. Converts it to greyscale and applies CLAHE contrast enhancement, which improves detection in poor light.
3. Detects markers and discards any with a side under 10 pixels (`MIN_SIDE_PX` in `main.py`).
4. Maps each ID to a label.
5. Logs each marker ID at most once per second (`WRITE_COOLDOWN_MS`), which keeps the CSV small. The limit uses real time, so a video that processes faster than it plays logs fewer rows.

Markers need a white border to be detected.

### Marker Labels

Labels are defined in `ARUCO_LABELS` in `main.py`. Other IDs appear as `unknown_N`.

| ID | Label |
|----|-------|
| 0 | `zone_de_decollage` |
| 1 | `robot` |
| 2-3 | `align` |
| 4-11 | `fenetre_facile_*` (recto/verso, droite/gauche, haut/bas) |
| 12-15 | `fenetre_difficile_*` (recto/verso, haut/bas) |

### Output

**Terminal, every 2 seconds:**
```
[14:32:01] detect=3.2ms
  ID= 0  label=zone_de_decollage                         center=(640.0,360.0)
  ID= 4  label=fenetre_facile_recto_droite_bas           center=(213.5,180.2)
```

**`detections.csv`:**
```
timestamp_ms,id,label,cx,cy
1710000000000,0,zone_de_decollage,640.0,360.0
```

**`aruco_debug.jpg`:** the latest frame with accepted markers drawn, updated every 2 seconds.

## Project Structure

```
Detect Aruco Realtime/
├── main.py                # Detection loop and command-line options
├── camera_opencv.py       # Any source cv2.VideoCapture can open
├── camera_rubikpi_csi.py  # RubikPi CSI camera (GStreamer pipeline)
├── camera_picamera2.py    # Raspberry Pi camera
├── make_test_video.py     # Generates a test video of moving markers
├── benchmark.py           # Scores detection against ground truth
├── test_main.py           # Unit and end-to-end tests
├── check.sh               # Runs all checks with short output
├── setup.sh               # Installs GStreamer and qtiqmmfsrc on the RubikPi
├── test_camera.sh         # Tests the CSI pipeline without OpenCV
├── build_opencv.sh        # Builds OpenCV with GStreamer and aruco
└── TODO.md                # Known problems and open work
```

## Test Footage

`make_test_video.py` output is easy to detect, so use real footage to judge detection quality. Footage belongs in `test_footage/` at the repository root, which git ignores.

Neither set below is drone footage or uses `DICT_4X4_50`, so both need `--dict`.

**Download, from the repository root:**
```bash
mkdir -p test_footage/fdcl-gwu test_footage/shadow-aruco
curl -L -o test_footage/fdcl-gwu/test_video.mp4 \
    https://raw.githubusercontent.com/fdcl-gwu/aruco-markers/master/test_data/test_video.mp4
curl -L https://zenodo.org/api/records/10791293/files/video_5.tar.gz/content \
    | tar -xz -C test_footage/shadow-aruco
```

**Run, from `Detect Aruco Realtime/`:**
```bash
python3 main.py --source ../test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL
python3 main.py --source "../test_footage/shadow-aruco/video_5/%05d.png" --dict DICT_ARUCO_MIP_36h12
```

| Set | Content | Source | License |
|-----|---------|--------|---------|
| `fdcl-gwu` | 821 frames at 1080p | [fdcl-gwu/aruco-markers](https://github.com/fdcl-gwu/aruco-markers) | BSD-3-Clause |
| `shadow-aruco` | 1,334 photos at 800×600 in a dark room with moving shadows, with ground truth in `corrected_annotations/` | [Shadow-ArUco Dataset](https://doi.org/10.5281/zenodo.10791293), `video_5` | CC BY 4.0 |

## Contributing

Contributors and coding agents follow [`AGENTS.md`](AGENTS.md). Work happens on branches, and each branch has a log in `logs/`.

**Agents:** read and use the project's Markdown files, opening only what the task needs:

- [`AGENTS.md`](AGENTS.md): rules for all work in this repository
- [`Detect Aruco Realtime/TODO.md`](Detect%20Aruco%20Realtime/TODO.md): known problems and open work
- [`logs/DECISIONS.md`](logs/DECISIONS.md): lasting decisions
- [`docs/contest-rules.md`](docs/contest-rules.md): provisional Droneload 2027 rules, for contest questions
- [`logs/`](logs/): one log per branch, where you record your work
- `README.md` or [`README.fr.md`](README.fr.md): what the project does and how to run it

Before asking for review, run these from `Detect Aruco Realtime/`:

```bash
pip install -r requirements-dev.txt
./check.sh
```

## RubikPi 3 Installation

**This procedure has not been confirmed on a board.**

On the RubikPi 3, the CSI camera is only reachable through `qtiqmmfsrc`, a Qualcomm GStreamer plugin, so OpenCV needs GStreamer support to read frames. The packaged versions each lack something:

- `apt install python3-opencv` has GStreamer, but incomplete aruco support.
- `pip install opencv-contrib-python` has aruco, but no GStreamer.

OpenCV therefore has to be compiled from source.

### 1. Clone the repository

```bash
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
cd "droneload-ESILV-2026-2027/Detect Aruco Realtime"
chmod +x setup.sh test_camera.sh build_opencv.sh
```

### 2. Install GStreamer and qtiqmmfsrc

```bash
./setup.sh
```

### 3. Test the camera

```bash
./test_camera.sh
```

Run this before compiling, which takes 1-2 hours. Press Ctrl+C after a few seconds. The script should print `Pipeline OK`.

If it fails, try `video/x-raw(memory:GBM)` with `qtivtransform` in place of plain `video/x-raw` with `videoconvert`. Make the same change in `camera_rubikpi_csi.py`, because both files must use the same pipeline.

### 4. Compile OpenCV

```bash
./build_opencv.sh
```

This builds OpenCV 4.10.0 with GStreamer and the contrib modules. Check that it ends with:

```
OpenCV version: 4.10.0
aruco OK: True
GStreamer: YES
```

### 5. Run

```bash
python3 main.py --source rubikpi-csi
```
