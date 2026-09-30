"""
PCB Inspection Dashboard.

Run with:
    streamlit run app/app.py
"""

from __future__ import annotations

import base64
import io
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from app.utils import (
        SEVERITY_STYLES,
        draw_bounding_boxes,
        evaluate_board_verdict,
        infer_severity,
        list_sample_images,
        load_demo_configs,
        prettify_class_name,
        validate_image_upload,
    )
except ImportError:
    from utils import (
        SEVERITY_STYLES,
        draw_bounding_boxes,
        evaluate_board_verdict,
        infer_severity,
        list_sample_images,
        load_demo_configs,
        prettify_class_name,
        validate_image_upload,
    )


WEIGHTS_PATH = Path("runs/B1_100ep/weights/best.pt")
THRESHOLD_PATH = Path("configs/threshold.yaml")
DATA_YAML_PATH = Path("data/data.yaml")
ABLATION_PATH = Path("results/ablation_master.csv") if Path("results/ablation_master.csv").exists() else Path("results/csv/ablation_master.csv")
LATENCY_PATH = Path("results/latency_summary.csv") if Path("results/latency_summary.csv").exists() else Path("results/csv/latency_summary.csv")
IMAGE_SIZE = 640
DEFAULT_CONF_THRESHOLD = 0.05


st.set_page_config(
    page_title="PCB Inspection Dashboard",
    page_icon="PCB",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #0b1220;
            --panel: #111a2b;
            --line: #233149;
            --muted: #94a3b8;
            --text: #e5edf8;
            --cyan: #22d3ee;
            --red: #ff4752;
            --green: #10b981;
        }

        html, body, [class*="css"] {
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: #0f1828;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: var(--text);
        }

        .block-container {
            padding-top: 1.15rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
        }

        .dash-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            border-bottom: 1px solid var(--line);
            margin: -6px 0 18px;
            padding-bottom: 16px;
        }

        .dash-title {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--text);
        }

        .station-pill {
            background: #1f293c;
            border: 1px solid var(--line);
            color: var(--text);
            border-radius: 6px;
            padding: 9px 14px;
            font-weight: 800;
            font-size: 0.82rem;
            text-transform: uppercase;
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 6px 22px;
            font-weight: 800;
            font-size: 1.08rem;
            color: var(--text);
        }

        .brand-mark {
            width: 38px;
            height: 38px;
            border-radius: 8px;
            border: 1px solid rgba(34, 211, 238, 0.55);
            display: grid;
            place-items: center;
            color: var(--cyan);
            font-weight: 900;
            box-shadow: 0 0 18px rgba(34, 211, 238, 0.18);
        }

        .nav-item {
            padding: 11px 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            color: #cbd5e1;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .nav-item.active {
            background: #233149;
            color: var(--cyan);
            border-color: #2b3f5f;
        }

        .side-card, .panel-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px;
        }

        .panel-title {
            color: var(--text);
            font-size: 0.92rem;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .metric-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
            min-height: 96px;
        }

        .metric-card.alert {
            background: linear-gradient(135deg, rgba(255, 71, 82, 0.28), rgba(17, 26, 43, 0.95));
            border-color: rgba(255, 71, 82, 0.5);
        }

        .metric-label {
            color: var(--muted);
            text-transform: uppercase;
            font-weight: 800;
            font-size: 0.78rem;
            margin-bottom: 8px;
        }

        .metric-value {
            color: var(--text);
            font-size: 1.86rem;
            line-height: 1.05;
            font-weight: 900;
        }

        .metric-value.defective, .metric-value.critical {
            color: var(--red);
        }

        .metric-value.pass {
            color: var(--green);
        }

        .image-shell {
            background: #1c2637;
            border: 1px solid #29384f;
            border-radius: 4px;
            padding: 10px;
        }

        .legend-row {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #dbeafe;
            margin: 7px 0;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .legend-dot {
            width: 13px;
            height: 13px;
            border-radius: 2px;
            display: inline-block;
        }

        .verdict-card {
            border-radius: 8px;
            padding: 20px;
            min-height: 195px;
            color: #0b1220;
        }

        .verdict-card.defective {
            background: #ff4752;
        }

        .verdict-card.pass {
            background: #10b981;
        }

        .verdict-card.ready {
            background: #334155;
            color: #e5edf8;
        }

        .verdict-title {
            font-size: 2.35rem;
            font-weight: 900;
            margin-bottom: 4px;
        }

        .verdict-subtitle {
            font-weight: 900;
            margin-bottom: 18px;
        }

        .verdict-lines {
            font-weight: 700;
            line-height: 1.7;
        }

        .status-online {
            display: inline-block;
            background: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 800;
        }

        .section-gap {
            height: 12px;
        }

        .stDataFrame {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }

        div[data-testid="stFileUploader"] section {
            background: #172238;
            border: 1px dashed #34506f;
        }

        div[data-testid="stDownloadButton"] button {
            background: #1f9cf0;
            color: white;
            border-radius: 6px;
            border: 1px solid #37b6ff;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def html_metric(label: str, value: str, value_class: str = "", alert: bool = False) -> None:
    alert_class = " alert" if alert else ""
    st.markdown(
        f"""
        <div class="metric-card{alert_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value {value_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_model_performance() -> dict[str, str]:
    values = {
        "mAP@0.5": "N/A",
        "mAP@0.5:0.95": "N/A",
        "Recall Small Defects": "N/A",
        "Recall Critical Defects": "N/A",
        "Critical False Negative Rate": "N/A",
        "Board False Accept": "N/A",
        "Avg Inference Time": "N/A",
    }

    if ABLATION_PATH.exists():
        ablation = pd.read_csv(ABLATION_PATH)
        proposed = ablation[ablation["code"].astype(str).str.lower() == "proposed"]
        if not proposed.empty:
            row = proposed.iloc[0]
            values.update(
                {
                    "mAP@0.5": f"{float(row['mAP@0.5']) * 100:.2f}%",
                    "mAP@0.5:0.95": f"{float(row['mAP@0.5:0.95']) * 100:.2f}%",
                    "Recall Small Defects": f"{float(row['R_small']) * 100:.2f}%",
                    "Recall Critical Defects": f"{float(row['R_critical']) * 100:.2f}%",
                    "Critical False Negative Rate": f"{float(row['Critical_FN_rate']) * 100:.2f}%",
                    "Board False Accept": f"{float(row['Board_FA']) * 100:.2f}%",
                }
            )

    if LATENCY_PATH.exists():
        latency = pd.read_csv(LATENCY_PATH)
        proposed_latency = latency[latency["code"].astype(str).str.lower() == "proposed"]
        if not proposed_latency.empty:
            values["Avg Inference Time"] = (
                f"{float(proposed_latency.iloc[0]['end_to_end_latency_ms_mean']):.2f} ms"
            )

    return values


def detection_dataframe(detections: list[dict[str, object]]) -> pd.DataFrame:
    if not detections:
        return pd.DataFrame(
            columns=["ID", "Defect Type", "Severity", "Confidence %", "Coordinates", "Status"]
        )

    rows = []
    for idx, det in enumerate(detections, start=1):
        rows.append(
            {
                "ID": idx,
                "Defect Type": prettify_class_name(str(det["class"])),
                "Severity": det["severity"],
                "Confidence %": f"{float(det['confidence']) * 100:.2f}%",
                "Coordinates": f"[{det['xmin']}, {det['ymin']}, {det['xmax']}, {det['ymax']}]",
                "Status": "Defect",
            }
        )
    return pd.DataFrame(rows)


def render_distribution_chart(detections: list[dict[str, object]]):
    severity_order = ["Critical", "High", "Medium", "Low"]
    counts = pd.Series([det["severity"] for det in detections]).value_counts()
    values = [int(counts.get(level, 0)) for level in severity_order]
    colors = [SEVERITY_STYLES[level]["hex"] for level in severity_order]

    fig, ax = plt.subplots(figsize=(5, 3.1), facecolor="#111a2b")
    ax.set_facecolor("#111a2b")
    ax.bar([level.lower() for level in severity_order], values, color=colors, width=0.62)
    ax.tick_params(colors="#cbd5e1", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#233149")
    ax.grid(axis="y", color="#233149", alpha=0.75)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(values + [1]) + 1)
    return fig


def image_to_data_uri(image, image_format: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    mime = "image/png" if image_format.upper() == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def zoomable_image(image, component_key: str, height: int = 650) -> None:
    safe_key = "".join(ch if ch.isalnum() else "_" for ch in component_key)
    data_uri = image_to_data_uri(image)
    components.html(
        f"""
        <div class="zoom-toolbar-{safe_key}">
          <span>Scroll to zoom • drag to pan</span>
          <button id="zoomOut-{safe_key}">-</button>
          <button id="zoomReset-{safe_key}">Reset</button>
          <button id="zoomIn-{safe_key}">+</button>
        </div>
        <div id="zoomWrap-{safe_key}" class="zoom-wrap-{safe_key}">
          <img id="zoomImg-{safe_key}" src="{data_uri}" draggable="false" />
        </div>
        <style>
          .zoom-toolbar-{safe_key} {{
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
            color: #cbd5e1;
            font: 600 13px Inter, system-ui, sans-serif;
            background: #172238;
            border: 1px solid #2c3d58;
            border-bottom: 0;
            border-radius: 6px 6px 0 0;
            padding: 0 10px;
            box-sizing: border-box;
          }}
          .zoom-toolbar-{safe_key} button {{
            background: #22324b;
            color: #e5edf8;
            border: 1px solid #34506f;
            border-radius: 5px;
            padding: 3px 9px;
            cursor: pointer;
            font-weight: 800;
          }}
          .zoom-wrap-{safe_key} {{
            height: {height}px;
            overflow: hidden;
            background: #0b1220;
            border: 1px solid #2c3d58;
            border-radius: 0 0 8px 8px;
            cursor: grab;
            position: relative;
            user-select: none;
          }}
          .zoom-wrap-{safe_key}:active {{
            cursor: grabbing;
          }}
          #zoomImg-{safe_key} {{
            max-width: 100%;
            max-height: 100%;
            position: absolute;
            left: 50%;
            top: 50%;
            transform-origin: center center;
            will-change: transform;
            image-rendering: auto;
          }}
        </style>
        <script>
          const wrap = document.getElementById("zoomWrap-{safe_key}");
          const img = document.getElementById("zoomImg-{safe_key}");
          const resetBtn = document.getElementById("zoomReset-{safe_key}");
          const inBtn = document.getElementById("zoomIn-{safe_key}");
          const outBtn = document.getElementById("zoomOut-{safe_key}");

          let scale = 1;
          let translateX = 0;
          let translateY = 0;
          let dragging = false;
          let lastX = 0;
          let lastY = 0;

          function applyTransform() {{
            img.style.transform = `translate(calc(-50% + ${{translateX}}px), calc(-50% + ${{translateY}}px)) scale(${{scale}})`;
          }}

          function clampScale(value) {{
            return Math.min(8, Math.max(0.4, value));
          }}

          function zoom(delta, clientX, clientY) {{
            const oldScale = scale;
            scale = clampScale(scale * delta);
            const rect = wrap.getBoundingClientRect();
            const offsetX = clientX - rect.left - rect.width / 2;
            const offsetY = clientY - rect.top - rect.height / 2;
            const scaleRatio = scale / oldScale;
            translateX = offsetX - (offsetX - translateX) * scaleRatio;
            translateY = offsetY - (offsetY - translateY) * scaleRatio;
            applyTransform();
          }}

          wrap.addEventListener("wheel", (event) => {{
            event.preventDefault();
            const delta = event.deltaY < 0 ? 1.12 : 0.88;
            zoom(delta, event.clientX, event.clientY);
          }}, {{ passive: false }});

          wrap.addEventListener("pointerdown", (event) => {{
            dragging = true;
            lastX = event.clientX;
            lastY = event.clientY;
            wrap.setPointerCapture(event.pointerId);
          }});

          wrap.addEventListener("pointermove", (event) => {{
            if (!dragging) return;
            translateX += event.clientX - lastX;
            translateY += event.clientY - lastY;
            lastX = event.clientX;
            lastY = event.clientY;
            applyTransform();
          }});

          wrap.addEventListener("pointerup", () => {{
            dragging = false;
          }});

          resetBtn.addEventListener("click", () => {{
            scale = 1;
            translateX = 0;
            translateY = 0;
            applyTransform();
          }});

          inBtn.addEventListener("click", () => {{
            const rect = wrap.getBoundingClientRect();
            zoom(1.18, rect.left + rect.width / 2, rect.top + rect.height / 2);
          }});

          outBtn.addEventListener("click", () => {{
            const rect = wrap.getBoundingClientRect();
            zoom(0.85, rect.left + rect.width / 2, rect.top + rect.height / 2);
          }});

          img.onload = applyTransform;
          applyTransform();
        </script>
        """,
        height=height + 40,
        scrolling=False,
    )


def render_sidebar(default_tau: float, sample_images: list[Path]) -> tuple[str, float]:
    st.sidebar.markdown(
        """
        <div class="brand-box">
            <div class="brand-mark">AI</div>
            <div>PCB Inspect AI</div>
        </div>
        <div class="nav-item active">Inspection</div>
        <div class="nav-item">History</div>
        <div class="nav-item">Analytics</div>
        <div class="nav-item">Model Performance</div>
        <div class="nav-item">Settings</div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    conf_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.01,
        max_value=0.50,
        value=float(default_tau),
        step=0.01,
        help="Điều chỉnh ngưỡng tin cậy phát hiện khuyết tật (Mặc định: 0.05).",
    )

    st.sidebar.markdown(
        f"""
        <div class="side-card">
            <div class="panel-title">Model Status</div>
            <div><b>Proposed:</b>&nbsp;&nbsp; YOLOv8n-P2</div>
            <div><b>Confidence Threshold:</b>&nbsp;&nbsp; {conf_threshold:.2f}</div>
            <div><b>Image Size:</b>&nbsp;&nbsp; {IMAGE_SIZE} px</div>
            <div><b>Status:</b>&nbsp;&nbsp; <span class="status-online">ONLINE</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    sample_options = ["Upload from computer"] + [str(path) for path in sample_images]
    default_index = 1 if sample_images else 0
    sample_choice = st.sidebar.selectbox(
        "Sample image",
        sample_options,
        index=default_index,
        help="Choose a built-in sample or upload your own PCB image.",
    )
    return sample_choice, conf_threshold


inject_css()

try:
    tau_b1, class_names, threshold_config = load_demo_configs(
        threshold_path=THRESHOLD_PATH,
        data_path=DATA_YAML_PATH,
    )
except Exception as exc:
    st.error(f"Could not load demo configuration: {exc}")
    st.stop()


@st.cache_resource
def load_model(weights_path: str):
    weights = Path(weights_path)
    if not weights.exists():
        raise FileNotFoundError(f"Missing Proposed checkpoint: {weights}")

    from ultralytics import YOLO

    return YOLO(str(weights))


sample_choice, current_tau = render_sidebar(DEFAULT_CONF_THRESHOLD, list_sample_images())

st.markdown(
    """
    <div class="dash-header">
        <div class="dash-title">PCB Inspection Dashboard</div>
        <div class="station-pill">Line 1 - Inspection Station</div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    model = load_model(str(WEIGHTS_PATH))
except Exception as exc:
    st.error(f"Could not load YOLO model: {exc}")
    st.stop()

target_image_file = None
image_source_name = ""

uploader_col, note_col = st.columns([2.2, 3])
with uploader_col:
    uploaded_file = st.file_uploader(
        "Upload PCB image",
        type=["jpg", "jpeg", "png", "bmp"],
        label_visibility="collapsed",
    )
with note_col:
    st.caption(
        "Accepted formats: JPG, PNG, BMP. The app uses the locked Proposed checkpoint and threshold. "
        "No threshold tuning is performed here."
    )

if uploaded_file is not None:
    target_image_file = uploaded_file
    image_source_name = uploaded_file.name
elif sample_choice != "Upload from computer":
    sample_path = Path(sample_choice)
    with sample_path.open("rb") as handle:
        target_image_file = io.BytesIO(handle.read())
    setattr(target_image_file, "name", sample_path.name)
    image_source_name = sample_path.name

if target_image_file is None:
    st.info("Upload an image or choose a sample image from the sidebar to start.")
    st.stop()

is_valid, error_message, input_image = validate_image_upload(target_image_file)
if not is_valid or input_image is None:
    st.error(error_message or "Invalid image.")
    st.stop()

image_key = f"{image_source_name}:{input_image.size[0]}x{input_image.size[1]}"
if st.session_state.get("active_image_key") != image_key:
    st.session_state["active_image_key"] = image_key
    st.session_state["scan_complete"] = False
    st.session_state["detections"] = []
    st.session_state["latency_ms"] = 0.0

action_col, hint_col = st.columns([1.2, 3])
with action_col:
    run_detection = st.button(
        "Generate Annotated Image",
        type="primary",
        use_container_width=True,
    )
with hint_col:
    st.caption(
        "Annotated Image is generated only after this button is clicked. "
        "Use mouse wheel on the image viewer to zoom in/out and drag to inspect small defects."
    )

if run_detection:
    detections_tmp: list[dict[str, object]] = []
    start_time = time.perf_counter()

    try:
        results = model.predict(
            input_image,
            imgsz=IMAGE_SIZE,
            conf=current_tau,
            verbose=False,
        )
    except Exception as exc:
        st.error(f"Inference failed: {exc}")
        st.stop()

    latency_ms = (time.perf_counter() - start_time) * 1000

    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            coords = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = class_names.get(class_id, f"class_{class_id}")
            severity = infer_severity(class_name)
            detections_tmp.append(
                {
                    "class": class_name,
                    "severity": severity,
                    "confidence": round(confidence, 4),
                    "xmin": round(float(coords[0]), 1),
                    "ymin": round(float(coords[1]), 1),
                    "xmax": round(float(coords[2]), 1),
                    "ymax": round(float(coords[3]), 1),
                }
            )

    st.session_state["scan_complete"] = True
    st.session_state["detections"] = detections_tmp
    st.session_state["latency_ms"] = latency_ms

detections = list(st.session_state.get("detections", []))
latency_ms = float(st.session_state.get("latency_ms", 0.0))
scan_complete = bool(st.session_state.get("scan_complete", False))

verdict, _verdict_color = evaluate_board_verdict(detections) if scan_complete else ("READY", "#94A3B8")
annotated_image = draw_bounding_boxes(input_image, detections) if scan_complete else None
avg_confidence = sum(float(det["confidence"]) for det in detections) / len(detections) if detections else 0.0
critical_count = sum(1 for det in detections if det["severity"] == "Critical")
det_df = detection_dataframe(detections)
performance = load_model_performance()

card_cols = st.columns(5)
with card_cols[0]:
    metric_class = "defective" if verdict == "DEFECTIVE" else "pass" if verdict == "PASS" else ""
    html_metric("Current Verdict", verdict, metric_class, verdict == "DEFECTIVE")
with card_cols[1]:
    html_metric("Total Defects", str(len(detections)) if scan_complete else "-")
with card_cols[2]:
    html_metric("Critical Defects", str(critical_count) if scan_complete else "-", "critical", critical_count > 0)
with card_cols[3]:
    html_metric("Inference Latency", f"{latency_ms:.2f} ms" if scan_complete else "-")
with card_cols[4]:
    html_metric("Avg Confidence", f"{avg_confidence * 100:.2f}%" if scan_complete else "-")

st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

main_left, main_right = st.columns([2.45, 1])

with main_left:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">PCB Image Viewer</div>', unsafe_allow_html=True)
    st.caption(f"{image_source_name} | {input_image.size[0]} x {input_image.size[1]} px")

    img_col, legend_col = st.columns([4.4, 1.1])
    with img_col:
        tab_original, tab_annotated = st.tabs(["Original", "Annotated Image"])
        with tab_original:
            st.markdown('<div class="image-shell">', unsafe_allow_html=True)
            zoomable_image(input_image, f"original-{image_key}", height=650)
            st.markdown("</div>", unsafe_allow_html=True)
        with tab_annotated:
            st.markdown('<div class="image-shell">', unsafe_allow_html=True)
            if scan_complete and annotated_image is not None:
                zoomable_image(annotated_image, f"annotated-{image_key}", height=650)
            else:
                st.info("Click Generate Annotated Image to run defect detection and show annotated boxes here.")
            st.markdown("</div>", unsafe_allow_html=True)

    with legend_col:
        st.markdown('<div class="panel-title">Legend</div>', unsafe_allow_html=True)
        for severity in ["Critical", "High", "Medium", "Low"]:
            st.markdown(
                f"""
                <div class="legend-row">
                    <span class="legend-dot" style="background:{SEVERITY_STYLES[severity]['hex']}"></span>
                    {severity.lower()}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Zoom Control:**")
        st.write("Scroll to zoom. Drag to pan. Use Reset to fit again.")

    if scan_complete and annotated_image is not None:
        buffer = io.BytesIO()
        annotated_image.save(buffer, format="JPEG", quality=95)
        dl_col, _ = st.columns([1.4, 3])
        with dl_col:
            st.download_button(
                label="Download Annotated Result",
                data=buffer.getvalue(),
                file_name=f"annotated_{Path(image_source_name).stem}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

with main_right:
    verdict_class = "defective" if verdict == "DEFECTIVE" else "pass" if verdict == "PASS" else "ready"
    verdict_subtitle = (
        "Board fails quality check"
        if verdict == "DEFECTIVE"
        else f"No detection above threshold ({current_tau:.2f})"
        if verdict == "PASS"
        else "Waiting for defect detection"
    )
    summary_lines = "<br>".join(
        f"{prettify_class_name(str(name))}: {count}"
        for name, count in pd.Series([det["class"] for det in detections]).value_counts().items()
    )
    if not scan_complete:
        summary_lines = "Click Generate Annotated Image"
    elif not summary_lines:
        summary_lines = "No defects detected"

    st.markdown(
        f"""
        <div class="verdict-card {verdict_class}">
            <div class="verdict-title">{verdict}</div>
            <div class="verdict-subtitle">{verdict_subtitle.upper()}</div>
            <div class="verdict-lines">
                Defect Summary:<br>{summary_lines}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Current Detections</div>', unsafe_allow_html=True)
    st.dataframe(
        det_df[["ID", "Defect Type", "Confidence %", "Severity", "Coordinates"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

bottom_left, bottom_mid, bottom_right = st.columns([1.7, 0.95, 1.05])
with bottom_left:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Inspection Results Detailed List</div>', unsafe_allow_html=True)
    st.dataframe(det_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_mid:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Defect Distribution by Severity</div>', unsafe_allow_html=True)
    st.pyplot(render_distribution_chart(detections), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Model Performance (Test Set)</div>', unsafe_allow_html=True)
    for key, value in performance.items():
        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;gap:12px;margin:7px 0;color:#dbeafe;">
                <span>{key}</span><b>{value}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Locked threshold details"):
    st.json(threshold_config)
