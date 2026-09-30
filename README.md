# PCB Defect Detection

Prototype and experiment repository for PCB defect detection with YOLOv8n, a P2 architectural variant, and validation-locked threshold optimization.

## Demo

Run the Streamlit dashboard:

```bash
streamlit run app/app.py
```

The dashboard uses the locked Proposed configuration:

- Checkpoint: `runs/B1_100ep/weights/best.pt`
- Threshold: `tau.B1` from `configs/threshold.yaml`
- Decision rule: if at least one detection remains after the threshold, the board is `DEFECTIVE`; otherwise it is `PASS`.
- Annotated output is generated only after clicking **Generate Annotated Image**.
- The image viewer supports mouse-wheel zoom and drag-to-pan for defect inspection.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

On Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r app\requirements.txt
```

## Quick Run

macOS/Linux:

```bash
bash app/run_app.sh
```

Windows:

```bat
app\run_app.bat
```

## Data Preparation

Expected data/config files:

```text
data/data.yaml
data/splits/train.txt
data/splits/val.txt
data/splits/test.txt
data/splits/split_manifest.json
configs/base.yaml
configs/yolov8n-p2.yaml
configs/threshold.yaml
```

The raw dataset is kept under `data/raw/`; converted YOLO labels are kept under `data/processed/labels/`. Do not modify `data/raw/`.

## Training And Evaluation

The main experiment notebooks are stored in `scripts/`:

```text
scripts/11_kaggle_train_B0_100ep.ipynb
scripts/15_kaggle_train_B1_100ep.ipynb
scripts/17_threshold_sweep_val.ipynb
scripts/18_ablation_test_locked.ipynb
scripts/19_ablation_analysis_figures.ipynb
scripts/20_error_analysis.ipynb
scripts/21_latency_pareto.ipynb
```

Main outputs:

```text
runs/B0_100ep/weights/best.pt
runs/B1_100ep/weights/best.pt
results/ablation_master.csv
results/latency_summary.csv
```

## Project Structure

```text
app/                 Streamlit demo
configs/             Training and threshold configs
data/                Dataset YAML, splits, raw/processed data
docs/                Hardware notes, data audit, decision log
results/             Evaluation tables, figures, reports
runs/                Training outputs and checkpoints
scripts/             Experiment notebooks
```

## Main Experiment Configurations

```text
B0       = YOLOv8n, default confidence threshold 0.25
B1       = YOLOv8n-P2, default confidence threshold 0.25
B2       = B0 weights + validation-selected tau_B0
Proposed = B1 weights + validation-selected tau_B1
```

B2 and Proposed do not require retraining. They apply the locked decision threshold to existing B0/B1 weights.

## Summary Results

From `results/ablation_master.csv`, the locked test-set comparison is:

```text
B0       mAP@0.5=66.73%, R_small=68.21%, R_critical=76.12%
B1       mAP@0.5=65.41%, R_small=69.50%, R_critical=79.50%
B2       mAP@0.5=66.73%, R_small=70.08%, R_critical=78.25%
Proposed mAP@0.5=65.41%, R_small=74.58%, R_critical=84.38%
```

The dashboard uses the Proposed row.

## Edge-case Tests For Dashboard

Before demo, verify:

```text
valid JPG/PNG/BMP image -> app runs
non-image file -> friendly validation error
corrupt image file -> friendly validation error
image larger than 6000 px in width/height -> friendly validation error
image with no detection over tau_B1 -> PASS
image with at least one detection over tau_B1 -> DEFECTIVE
```

## Reproducibility Notes

- Split files are stored in `data/splits/`.
- Split checksum manifest is stored in `data/splits/split_manifest.json`.
- Threshold selection is documented in `configs/threshold.yaml`.
- Key decisions are recorded in `docs/decision_log.md`.
- Hardware details are recorded in `docs/hardware.md`.
- Scope, split, metric, and latency interpretation limits are recorded in `docs/project_scope_and_limitations.md`.

## Limitations

- The dashboard is a local prototype for thesis demonstration, not a production AOI system.
- `PASS` means no detection exceeded the locked threshold; it does not imply independent electrical validation.
- Formal latency should be reported from the Week 12 latency protocol, not from the interactive dashboard alone.
- The dataset has no independent defect-free PASS boards, so Board_FR is not evaluated in the thesis metrics.
