# Droneload: Real-Time ArUco Marker Detection

**English** | [Français](README.fr.md)

Droneload is the software for our entry in the Droneload 2027 contest, a student competition run by Planète Sciences. Teams build a multirotor that flies missions on its own indoors: it reads ArUco markers, drops light objects on targets and works with a ground robot.

So far, this repository contains the ArUco detection. It reads a camera or recorded footage, labels each marker, and logs the marker's centre in pixels. It does not estimate pose or distance yet, and it sends nothing to a flight controller. It was written for the RubikPi 3 (Qualcomm QCS6490), but runs on any machine with OpenCV.

## Project Structure

```
droneload/
├── flight/  navigation/  payload/  comms/  mission/   # Planned
└── vision/                     # Marker detection
    ├── detect.py               # Detection loop and command-line options
    ├── camera_opencv.py        # Any source cv2.VideoCapture can open
    ├── camera_rubikpi_csi.py   # RubikPi CSI camera (GStreamer pipeline)
    └── camera_picamera2.py     # Raspberry Pi camera
testing/
├── make_test_video.py          # Generates a test video of moving markers
└── benchmark.py                # Scores detection against ground truth
tests/                          # Unit and end-to-end tests
scripts/
├── check.sh                    # Runs all checks with short output
├── setup.sh                    # Installs GStreamer and qtiqmmfsrc on the RubikPi
├── test_camera.sh              # Tests the CSI pipeline without OpenCV
└── build_opencv.sh             # Builds OpenCV with GStreamer and aruco
docs/                           # Architecture and contest rules
logs/                           # Branch logs and decisions
TODO.md                         # Known problems and open work
```

`flight`, `navigation`, `payload`, `comms` and `mission` are planned and hold only a short README. See [`docs/architecture.md`](docs/architecture.md).

## Installation

Follow the section for your computer. You only do this once. To run the project on a RubikPi, see [RubikPi 3 Installation](#rubikpi-3-installation).

### Mac

**1. Install the tools.** Skip any you already have.

- Python 3: download it from [python.org/downloads](https://www.python.org/downloads/) and run the installer.
- Visual Studio Code: download it from [code.visualstudio.com](https://code.visualstudio.com/) and drag it into Applications.

**2. Open Terminal.** Press Cmd+Space, type `Terminal`, and press Return.

**3. Install Git and download the project.** Run these commands one at a time. If the first says the tools are already installed, carry on. Otherwise, click **Install** in the window that appears and wait for it to finish.

```bash
xcode-select --install
cd ~/Documents
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
```

**4. Go to the project folder.**

```bash
cd droneload-ESILV-2026-2027
```

**5. Open the project in VS Code.** Open VS Code, press Cmd+Shift+P, type `Shell Command: Install 'code' command in PATH`, and press Return. Then go back to Terminal and run:

```bash
code .
```

**6. Set up Python.** In VS Code, choose **Terminal > New Terminal**, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

The line in the terminal now starts with `(.venv)`. Run the `source` line again each time you open a new terminal.

**7. Test it.** This needs no camera:

```bash
python -m testing.make_test_video
python -m droneload.vision --source test_markers.mp4
```

The last line should say `Detections saved to detections.csv`. The results are in `detections.csv` and `aruco_debug.jpg`.

### Windows

**1. Install the tools.** Skip any you already have.

- Git: download it from [git-scm.com](https://git-scm.com/downloads) and accept the default options.
- Python 3: download it from [python.org/downloads](https://www.python.org/downloads/). On the first screen of the installer, tick **Add python.exe to PATH**.
- Visual Studio Code: download it from [code.visualstudio.com](https://code.visualstudio.com/) and accept the default options.

**2. Open PowerShell.** Press the Windows key, type `PowerShell`, and press Enter. If it was already open, close it and open it again so it finds the new tools.

**3. Download the project.** Run these commands one at a time:

```powershell
cd $HOME\Documents
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
```

**4. Go to the project folder.**

```powershell
cd droneload-ESILV-2026-2027
```

**5. Open the project in VS Code.**

```powershell
code .
```

**6. Set up Python.** In VS Code, choose **Terminal > New Terminal**, then run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

If the second line says that running scripts is disabled, run this once, then run that line again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

The line in the terminal now starts with `(.venv)`. Run the `Activate.ps1` line again each time you open a new terminal.

**7. Test it.** This needs no camera:

```powershell
python -m testing.make_test_video
python -m droneload.vision --source test_markers.mp4
```

The last line should say `Detections saved to detections.csv`. The results are in `detections.csv` and `aruco_debug.jpg`.

## Status

| Part | State |
|------|-------|
| Detection, labels and logging | Tested on a PC with generated and real footage |
| RubikPi CSI camera | Not tested on a board; the pipeline may need changing |
| Hardware | Assuming the organisers' loan kit; companion computer and cameras not chosen |
| Project markers (`DICT_4X4_50`) | Not tested on real footage |

On the Shadow-ArUco test footage, the detector found 56% of annotated markers, and 27% of its detections did not match the annotations. That footage uses a different dictionary, so these figures may not apply to project markers. `TODO.md` tracks open work.

## Usage

```bash
python -m droneload.vision [--source SOURCE] [--dict DICTIONARY]
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
3. Detects markers and discards any with a side under 10 pixels (`MIN_SIDE_PX` in `detect.py`).
4. Maps each ID to a label.
5. Logs each marker ID at most once per second (`WRITE_COOLDOWN_MS`), which keeps the CSV small. The limit uses real time, so a video that processes faster than it plays logs fewer rows.

Markers need a white border to be detected.

### Marker Labels

Labels are defined in `ARUCO_LABELS` in `detect.py`. Other IDs appear as `unknown_N`.

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

## Test Footage

`testing/make_test_video.py` output is easy to detect, so use real footage to judge detection quality. Footage belongs in `test_footage/` at the repository root, which git ignores.

Neither set below is drone footage or uses `DICT_4X4_50`, so both need `--dict`.

**Download.** On Windows, run this in **Git Bash**:
```bash
mkdir -p test_footage/fdcl-gwu test_footage/shadow-aruco
curl -L -o test_footage/fdcl-gwu/test_video.mp4 \
    https://raw.githubusercontent.com/fdcl-gwu/aruco-markers/master/test_data/test_video.mp4
curl -L https://zenodo.org/api/records/10791293/files/video_5.tar.gz/content \
    | tar -xz -C test_footage/shadow-aruco
```

**Run:**
```bash
python -m droneload.vision --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL
python -m droneload.vision --source "test_footage/shadow-aruco/video_5/%05d.png" --dict DICT_ARUCO_MIP_36h12
```

| Set | Content | Source | License |
|-----|---------|--------|---------|
| `fdcl-gwu` | 821 frames at 1080p | [fdcl-gwu/aruco-markers](https://github.com/fdcl-gwu/aruco-markers) | BSD-3-Clause |
| `shadow-aruco` | 1,334 photos at 800×600 in a dark room with moving shadows, with ground truth in `corrected_annotations/` | [Shadow-ArUco Dataset](https://doi.org/10.5281/zenodo.10791293), `video_5` | CC BY 4.0 |

## Contributing

Contributors and coding agents follow [`AGENTS.md`](AGENTS.md). Work happens on branches, and each branch has a log in `logs/`.

**Agents:** read and use the project's Markdown files, opening only what the task needs:

- [`AGENTS.md`](AGENTS.md): rules for all work in this repository
- [`TODO.md`](TODO.md): known problems and open work
- [`docs/architecture.md`](docs/architecture.md): modules and how they depend on each other
- [`logs/DECISIONS.md`](logs/DECISIONS.md): lasting decisions
- [`docs/contest-rules.md`](docs/contest-rules.md): provisional Droneload 2027 rules, for contest questions
- [`logs/`](logs/): one log per branch, where you record your work
- `README.md`: what the project does and how to run it

Before asking for review, run:

```bash
./scripts/check.sh
```

On Windows, run it in **Git Bash** instead of PowerShell, from the project folder:

```bash
source .venv/Scripts/activate
bash scripts/check.sh
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
cd droneload-ESILV-2026-2027
```

### 2. Install GStreamer and qtiqmmfsrc

```bash
./scripts/setup.sh
```

### 3. Test the camera

```bash
./scripts/test_camera.sh
```

Run this before compiling, which takes 1-2 hours. Press Ctrl+C after a few seconds. The script should print `Pipeline OK`.

If it fails, try `video/x-raw(memory:GBM)` with `qtivtransform` in place of plain `video/x-raw` with `videoconvert`. Make the same change in `droneload/vision/camera_rubikpi_csi.py`, because both files must use the same pipeline.

### 4. Compile OpenCV

```bash
./scripts/build_opencv.sh
```

This builds OpenCV 4.10.0 with GStreamer and the contrib modules. Check that it ends with:

```
OpenCV version: 4.10.0
aruco OK: True
GStreamer: YES
```

### 5. Run

```bash
python3 -m droneload.vision --source rubikpi-csi
```
