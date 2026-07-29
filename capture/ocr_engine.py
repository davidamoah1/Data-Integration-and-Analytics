"""OCR engine abstraction for the Smart Data Capture platform.

Uses `pytesseract` (a thin wrapper around the Tesseract OCR binary) for text
extraction with per-word confidence and bounding boxes, and `PyMuPDF` (pure
pip-installable, no external binary) to rasterize PDF pages to images before
OCR.

IMPORTANT — system dependency: Tesseract OCR must be installed separately on
the host machine (it is NOT installable via pip). If it is missing, OCR
calls raise `OcrUnavailableError` with a clear message instead of crashing
the whole pipeline; callers should catch this and mark the document as
`failed` with an actionable error message.

This module is intentionally the only place that talks to the OCR backend,
so a cloud OCR provider (Azure Document Intelligence, Google Vision, AWS
Textract — all of which handle handwriting far better than Tesseract) can be
swapped in later without touching classification/extraction/validation code.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class OcrUnavailableError(RuntimeError):
    """Raised when the OCR backend (Tesseract binary) is not available."""


@dataclass
class OcrWord:
    text: str
    confidence: float  # 0..1
    page: int
    left: float  # normalized 0..1
    top: float
    width: float
    height: float


@dataclass
class OcrResult:
    full_text: str
    words: list[OcrWord] = field(default_factory=list)
    mean_confidence: float = 0.0
    page_count: int = 1


def _get_pytesseract():
    try:
        import pytesseract
    except ImportError as e:
        raise OcrUnavailableError(
            "pytesseract is not installed. Run `pip install pytesseract` and "
            "install the Tesseract OCR binary (see https://github.com/tesseract-ocr/tesseract)."
        ) from e

    try:
        import config

        if getattr(config, "TESSERACT_CMD", ""):
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    except Exception:
        pass

    return pytesseract


def is_ocr_available() -> bool:
    """Return True if the Tesseract OCR binary is installed and reachable."""
    try:
        pytesseract = _get_pytesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        logger.warning("OCR backend unavailable: %s", e)
        return False


def render_pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> list[str]:
    """Rasterize each page of a PDF to a PNG image and return the file paths."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError(
            "PyMuPDF is not installed. Run `pip install PyMuPDF` to enable PDF support."
        ) from e

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    output_paths: list[str] = []

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            out_path = os.path.join(output_dir, f"{base}_page{page_index + 1}.png")
            pix.save(out_path)
            output_paths.append(out_path)

    return output_paths


def run_ocr_on_image(image_path: str, page: int = 1, lang: str = "eng") -> OcrResult:
    """Run OCR on a single image file and return text + word-level confidence/boxes."""
    pytesseract = _get_pytesseract()
    from PIL import Image

    try:
        img = Image.open(image_path)
    except Exception as e:
        raise RuntimeError(f"Could not open image for OCR: {e}") from e

    try:
        full_text = pytesseract.image_to_string(img, lang=lang)
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
    except Exception as e:
        raise OcrUnavailableError(
            "Tesseract OCR binary is not installed or not on PATH. "
            "Install it and/or set the TESSERACT_CMD environment variable. "
            f"Underlying error: {e}"
        ) from e

    img_w, img_h = img.size
    words: list[OcrWord] = []
    confidences: list[float] = []

    n = len(data.get("text", []))
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0
        if conf < 0:
            continue
        left, top, width, height = (
            data["left"][i],
            data["top"][i],
            data["width"][i],
            data["height"][i],
        )
        words.append(
            OcrWord(
                text=text,
                confidence=conf / 100.0,
                page=page,
                left=left / img_w if img_w else 0.0,
                top=top / img_h if img_h else 0.0,
                width=width / img_w if img_w else 0.0,
                height=height / img_h if img_h else 0.0,
            )
        )
        confidences.append(conf / 100.0)

    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return OcrResult(full_text=full_text, words=words, mean_confidence=mean_conf, page_count=1)


def run_ocr_on_document(image_paths: list[str], lang: str = "eng") -> OcrResult:
    """Run OCR across multiple page images and merge the results."""
    all_text: list[str] = []
    all_words: list[OcrWord] = []
    all_conf: list[float] = []

    for page_num, path in enumerate(image_paths, start=1):
        result = run_ocr_on_image(path, page=page_num, lang=lang)
        all_text.append(result.full_text)
        all_words.extend(result.words)
        if result.words:
            all_conf.append(result.mean_confidence)

    mean_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0

    return OcrResult(
        full_text="\n\n".join(all_text),
        words=all_words,
        mean_confidence=mean_conf,
        page_count=len(image_paths),
    )
