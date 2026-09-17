"""Step 3 — Extract the content.

Each page gets routed to the extractor that matches its type:
  text    -> PyMuPDF text extraction
  table   -> pdfplumber table extraction (kept as structured rows, not
             flattened into meaningless text)
  scanned -> OpenCV preprocessing + Tesseract OCR
  mixed   -> both text and table extraction
"""
import io
import os
import shutil
from dataclasses import dataclass, field

import cv2
import fitz
import numpy as np
import pdfplumber
import pytesseract
from PIL import Image

from .classifier import PageAssessment

# On Windows, Tesseract usually isn't on PATH even after installing it.
# Try the default install location automatically so users don't have to
# edit PATH by hand. Can be overridden with the TESSERACT_CMD env var.
_env_cmd = os.environ.get("TESSERACT_CMD")
_default_windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if _env_cmd:
    pytesseract.pytesseract.tesseract_cmd = _env_cmd
elif os.name == "nt" and shutil.which("tesseract") is None and os.path.isfile(_default_windows_path):
    pytesseract.pytesseract.tesseract_cmd = _default_windows_path


@dataclass
class PageExtraction:
    page_number: int
    page_type: str
    text: str = ""
    tables: list = field(default_factory=list)   # list[list[list[str]]]
    ocr_confidence: float | None = None
    notes: str = ""


def extract_page(pdf_path: str, assessment: PageAssessment) -> PageExtraction:
    doc = fitz.open(pdf_path)
    page = doc[assessment.page_number - 1]

    result = PageExtraction(page_number=assessment.page_number, page_type=assessment.page_type)

    if assessment.page_type in ("text", "mixed"):
        result.text = page.get_text("text") or ""

    if assessment.page_type in ("table", "mixed"):
        result.tables = _extract_tables(pdf_path, assessment.page_number)
        if not result.text:
            result.text = _tables_to_text(result.tables)

    if assessment.page_type == "scanned":
        ocr_text, conf = _ocr_page(page)
        result.text = ocr_text
        result.ocr_confidence = conf
        result.notes = "Extracted via OCR (scanned page)."

    doc.close()
    return result


def _extract_tables(pdf_path: str, page_number: int) -> list:
    tables_out = []
    with pdfplumber.open(pdf_path) as pdf:
        plumber_page = pdf.pages[page_number - 1]
        for tbl in plumber_page.extract_tables():
            cleaned = [[(cell or "").strip() for cell in row] for row in tbl]
            tables_out.append(cleaned)
    return tables_out


def _tables_to_text(tables: list) -> str:
    """Represent tables as text while keeping row relationships (not flattened blobs)."""
    lines = []
    for t_idx, table in enumerate(tables):
        lines.append(f"[Table {t_idx + 1}]")
        for row in table:
            lines.append(" | ".join(row))
    return "\n".join(lines)


def _ocr_page(page: "fitz.Page", zoom: float = 2.5) -> tuple[str, float]:
    """Render a PDF page to an image, then delegate to the shared OCR routine."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    np_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return ocr_image(np_img)


def ocr_image(np_img: np.ndarray) -> tuple[str, float]:
    """Shared OCR routine: OpenCV cleanup + Tesseract. Used for both scanned
    PDF pages and directly-uploaded image files, so there's one OCR
    implementation rather than two.

    Fails soft (empty text, 0 confidence) if Tesseract isn't installed,
    rather than crashing the whole document's processing.
    """
    cleaned = _preprocess_for_ocr(np_img)

    try:
        data = pytesseract.image_to_data(cleaned, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError:
        return "", 0.0

    words, confidences = [], []
    for word, conf in zip(data["text"], data["conf"]):
        if word.strip():
            words.append(word)
            try:
                c = float(conf)
                if c >= 0:
                    confidences.append(c)
            except (ValueError, TypeError):
                pass

    text = " ".join(words)
    avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.3
    return text, round(avg_conf, 3)


def _preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    """Step 3.5 — OpenCV cleanup: grayscale, denoise, adaptive threshold."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    return thresh
