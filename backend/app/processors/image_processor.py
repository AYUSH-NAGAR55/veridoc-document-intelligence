"""Image processor for directly-uploaded PNG/JPG/JPEG files. Reuses the
same OpenCV-preprocess + Tesseract OCR routine the PDF pipeline uses for
scanned pages — one OCR implementation, two entry points.
"""
import cv2
import numpy as np
from PIL import Image

from .base import DocumentProcessor
from ..pipeline.extractor import ocr_image
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class ImageProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        pil_img = Image.open(file_path).convert("RGB")
        np_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        text, confidence = ocr_image(np_img)

        unit = ContentUnit(
            location=Location(image="image_1"),
            text=text,
            content_type="scanned",
            ocr_confidence=confidence,
            notes="Extracted via OCR." if text else "No text could be read from this image.",
        )
        return NormalizedDocument(units=[unit], unit_count_label="images")
