"""Image preprocessing pipeline for the Smart Data Capture platform.

Uses Pillow only (no system binaries required beyond Python packages) to
improve OCR accuracy: grayscale conversion, auto-contrast, noise reduction,
sharpening, and simple deskew via projection-profile rotation search.

Perspective correction and shadow removal in the strict computer-vision
sense require OpenCV/deep-learning models; this module implements the
brightness/contrast/sharpness improvements that meaningfully help OCR today,
and is structured so a more advanced CV backend can be swapped in later
without changing callers (see `enhance_image`).
"""

from __future__ import annotations

import logging
import os

from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

MAX_DIMENSION = 3000  # cap very large photos for speed


def _load_image(path: str) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # auto-rotate based on camera EXIF orientation
    return img.convert("RGB")


def _resize_if_needed(img: Image.Image) -> Image.Image:
    w, h = img.size
    if max(w, h) <= MAX_DIMENSION:
        return img
    scale = MAX_DIMENSION / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _estimate_skew_angle(gray: Image.Image) -> float:
    """Estimate small rotation skew using a coarse projection-profile search.

    Rotates the image across a small angle range and picks the angle that
    maximizes the variance of horizontal row-sum profiles (text lines create
    sharp peaks/troughs when properly aligned).
    """
    import numpy as np

    small = gray.resize((min(gray.width, 600), min(gray.height, 800)))
    best_angle = 0.0
    best_score = -1.0
    for angle in range(-5, 6):
        rotated = small.rotate(angle, expand=False, fillcolor=255)
        arr = np.asarray(rotated, dtype=np.float32)
        row_sums = arr.sum(axis=1)
        score = float(np.var(row_sums))
        if score > best_score:
            best_score = score
            best_angle = float(angle)
    return best_angle


def enhance_image(input_path: str, output_path: str) -> dict:
    """Run the enhancement pipeline and write the result to `output_path`.

    Returns metadata about the operations applied.
    """
    img = _load_image(input_path)
    img = _resize_if_needed(img)

    gray = ImageOps.grayscale(img)

    skew_angle = _estimate_skew_angle(gray)
    if abs(skew_angle) >= 1:
        gray = gray.rotate(skew_angle, expand=True, fillcolor=255)
    else:
        skew_angle = 0.0

    # Denoise slightly, then boost contrast and sharpen text edges.
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gray.save(output_path, quality=95)

    return {
        "deskew_angle": skew_angle,
        "final_size": gray.size,
        "operations": [
            "exif_autorotate",
            "grayscale",
            "deskew",
            "denoise",
            "autocontrast",
            "sharpen",
        ],
    }


def make_thumbnail(input_path: str, output_path: str, size: tuple[int, int] = (320, 320)) -> None:
    img = _load_image(input_path)
    img.thumbnail(size, Image.LANCZOS)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=85)
