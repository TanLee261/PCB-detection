"""
Utilities for the Streamlit PCB defect detection demo.

The demo intentionally stays small: validate one uploaded image, run the locked
Proposed model, draw boxes, and apply the board-level PASS/DEFECTIVE rule.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw, ImageFont


VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
SEVERITY_STYLES = {
    "Critical": {"color": (239, 68, 68), "hex": "#EF4444"},
    "High": {"color": (245, 158, 11), "hex": "#F59E0B"},
    "Medium": {"color": (34, 211, 238), "hex": "#22D3EE"},
    "Low": {"color": (59, 130, 246), "hex": "#3B82F6"},
}


def prettify_class_name(class_name: str) -> str:
    return class_name.replace("_", " ").title()


def infer_severity(class_name: str) -> str:
    if class_name in {"open_circuit", "short"}:
        return "Critical"
    if class_name in {"missing_hole"}:
        return "High"
    if class_name in {"mouse_bite", "spur"}:
        return "Medium"
    return "Low"


def load_yaml(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Missing required config file: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {yaml_path}")
    return data


def load_demo_configs(
    threshold_path: str | Path = "configs/threshold.yaml",
    data_path: str | Path = "data/data.yaml",
) -> tuple[float, dict[int, str], dict[str, Any]]:
    """Load the locked Proposed threshold and class names without hardcoding."""
    threshold_cfg = load_yaml(threshold_path)
    tau_b1 = None

    if isinstance(threshold_cfg.get("tau"), dict) and "B1" in threshold_cfg["tau"]:
        tau_b1 = threshold_cfg["tau"]["B1"]
    elif "tau_B1" in threshold_cfg:
        tau_b1 = threshold_cfg["tau_B1"]

    if tau_b1 is None:
        raise KeyError("Could not find tau.B1 or tau_B1 in configs/threshold.yaml")

    data_cfg = load_yaml(data_path)
    names = data_cfg.get("names")
    if not names:
        raise KeyError("Could not find class names in data/data.yaml")

    if isinstance(names, list):
        class_names = {idx: str(name) for idx, name in enumerate(names)}
    elif isinstance(names, dict):
        class_names = {int(idx): str(name) for idx, name in names.items()}
    else:
        raise TypeError("data/data.yaml names must be either a list or mapping")

    return float(tau_b1), class_names, threshold_cfg


def validate_image_upload(
    uploaded_file: Any,
    max_dim: int = 6000,
    max_size_mb: int = 20,
) -> tuple[bool, str | None, Image.Image | None]:
    """Validate uploaded image content and return an RGB PIL image."""
    if uploaded_file is None:
        return False, "Please choose an image file.", None

    filename = str(getattr(uploaded_file, "name", "")).lower()
    if not filename.endswith(VALID_IMAGE_EXTENSIONS):
        return (
            False,
            "Invalid image format. Please upload .jpg, .jpeg, .png, or .bmp.",
            None,
        )

    if hasattr(uploaded_file, "getvalue"):
        file_bytes = uploaded_file.getvalue()
    else:
        file_bytes = uploaded_file.read()

    if not file_bytes:
        return False, "The uploaded file is empty.", None

    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return (
            False,
            f"Image is too large ({file_size_mb:.1f} MB). Maximum allowed size is {max_size_mb} MB.",
            None,
        )

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except Exception:
        return False, "Could not read this image. The file may be corrupted.", None

    image = image.convert("RGB")
    width, height = image.size
    if width > max_dim or height > max_dim:
        return (
            False,
            f"Image dimensions are too large ({width}x{height}px). Maximum dimension is {max_dim}px.",
            None,
        )

    return True, None, image


def draw_bounding_boxes(
    image: Image.Image,
    detections: list[dict[str, Any]],
) -> Image.Image:
    """Draw detection boxes, class labels, and confidence scores."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()

    text_color = (255, 255, 255)

    for det in detections:
        xmin = float(det["xmin"])
        ymin = float(det["ymin"])
        xmax = float(det["xmax"])
        ymax = float(det["ymax"])
        class_name = str(det["class"])
        confidence = float(det["confidence"])
        severity = str(det.get("severity", infer_severity(class_name)))
        box_color = SEVERITY_STYLES.get(severity, SEVERITY_STYLES["Low"])["color"]
        text_bg_color = tuple(max(0, channel - 45) for channel in box_color)

        for offset in range(3):
            draw.rectangle(
                [xmin - offset, ymin - offset, xmax + offset, ymax + offset],
                outline=box_color,
            )

        label = f"{class_name} {confidence:.2f}"
        text_bbox = draw.textbbox((xmin, max(0, ymin - 16)), label, font=font)
        draw.rectangle(text_bbox, fill=text_bg_color)
        draw.text((text_bbox[0] + 2, text_bbox[1]), label, fill=text_color, font=font)

    return annotated


def evaluate_board_verdict(detections: list[dict[str, Any]]) -> tuple[str, str]:
    """Board-level rule: any post-threshold detection means DEFECTIVE."""
    if detections:
        return "DEFECTIVE", "#EF4444"
    return "PASS", "#10B981"


def list_sample_images(sample_dir: str | Path = "app/sample_images") -> list[Path]:
    path = Path(sample_dir)
    if not path.exists():
        return []
    return sorted(
        item
        for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in VALID_IMAGE_EXTENSIONS
    )
