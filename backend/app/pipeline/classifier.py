"""Step 2 — Understand the PDF.

For every page we decide whether it is normal text, a scanned image that
needs OCR, or a page dominated by a table. This drives which extractor
runs on the page in the next step.
"""
from dataclasses import dataclass

import fitz  # PyMuPDF
import pdfplumber


@dataclass
class PageAssessment:
    page_number: int
    page_type: str          # "text" | "scanned" | "table" | "mixed"
    text_char_count: int
    image_area_ratio: float
    table_count: int


def classify_pdf(pdf_path: str) -> list[PageAssessment]:
    assessments: list[PageAssessment] = []

    doc = fitz.open(pdf_path)
    with pdfplumber.open(pdf_path) as plumber_pdf:
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            text_char_count = len(text.strip())

            page_rect_area = page.rect.width * page.rect.height
            image_area = 0.0
            for img in page.get_images(full=True):
                try:
                    xref = img[0]
                    bbox_list = page.get_image_rects(xref)
                    for rect in bbox_list:
                        image_area += rect.width * rect.height
                except Exception:
                    continue
            image_area_ratio = min(image_area / page_rect_area, 1.0) if page_rect_area else 0.0

            table_count = 0
            try:
                plumber_page = plumber_pdf.pages[i]
                tables = plumber_page.find_tables()
                table_count = len(tables)
            except Exception:
                table_count = 0

            page_type = _decide_type(text_char_count, image_area_ratio, table_count)

            assessments.append(PageAssessment(
                page_number=i + 1,
                page_type=page_type,
                text_char_count=text_char_count,
                image_area_ratio=round(image_area_ratio, 3),
                table_count=table_count,
            ))
    doc.close()
    return assessments


def _decide_type(text_chars: int, image_ratio: float, table_count: int) -> str:
    # Very little extractable text but a big embedded image -> scanned page.
    if text_chars < 40 and image_ratio > 0.4:
        return "scanned"
    if table_count > 0 and text_chars < 400:
        return "table"
    if table_count > 0 and text_chars >= 400:
        return "mixed"
    if text_chars < 40 and image_ratio <= 0.4:
        # Sparse but not clearly an image dump either — still worth an OCR pass
        # if a real render shows content; treated as scanned to be safe.
        return "scanned" if image_ratio > 0.05 else "text"
    return "text"
