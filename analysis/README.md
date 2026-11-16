# Analysis

Studies behind decisions, written to be rerun and shown in the project report. Each study has its own folder, with a notebook that walks through the steps, the Python code it calls, and an `output/` folder for charts. Git ignores `output/`.

## Setup

From the repository root, after the README's installation steps:

```bash
pip install -r analysis/requirements.txt
jupyter lab analysis/smoothing/smoothing_study.ipynb
```

Then run all cells. The notebooks need the test footage (README, "Test Footage"). PNG export needs a Chromium-based browser (Chrome, Chromium, Edge, Brave or Vivaldi). Without one, run `plotly_get_chrome` once. HTML charts work without it.

CI and the drone do not install these packages. Keep plotting code out of `droneload/` and `testing/`.

## Studies

| Folder | Question | Result |
|---|---|---|
| `smoothing/` | How does the tracker's `SMOOTHING` weight change position error and jitter under camera shake? | For per-frame positions it adds lag (4-9× the frame error at 0.6); on a still scene it gives a steadier estimate. It never changes which markers are reported. See the notebook's conclusion |

## Smoothing study

- `study.py`: shakes the footage with `testing/vibration_test.py`, detects once per level and seed, replays the detections through one tracker per weight, and computes the measures. It uses numpy only, and its tests are in `tests/test_smoothing_study.py`.
- `charts.py`: the Plotly charts, plus `save()` to write them as HTML and PNG.
- `smoothing_study.ipynb`: the walkthrough.

The first run takes about 6 minutes on a PC, then reads from `output/*.pkl`. The cache file name holds the seeds and a format version. Delete the `.pkl` files, or call `study.load_or_detect(name, refresh=True)`, after changing detection or the shake simulation.

Commit notebooks with outputs cleared:

```bash
jupyter nbconvert --clear-output --inplace analysis/smoothing/smoothing_study.ipynb
```
