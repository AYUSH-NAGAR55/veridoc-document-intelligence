"""OCR wrapper. Default engine is Tesseract (lightweight, easy to install).
Kept behind a small function-based interface so swapping in PaddleOCR later
only means changing this file."""
import io

import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.config import get_settings

_settings = get_settings()
if _settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _settings.tesseract_cmd


def _preprocess(np_image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY) if np_image.ndim == 3 else np_image
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def ocr_image_bytes(image_bytes: bytes) -> str:
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        np_img = np.array(pil_img)
        processed = _preprocess(np_img)
        return pytesseract.image_to_string(processed)
    except Exception:
        # OCR failures should degrade gracefully, not crash the pipeline.
        return ""


def ocr_image_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return ocr_image_bytes(f.read())
    except Exception:
        return ""
