import fitz  # PyMuPDF
import pdfplumber

from app.services.processors.base import BaseProcessor, ProcessingResult, RawContentUnit
from app.services.ocr_service import ocr_image_bytes

MIN_CHARS_BEFORE_OCR = 20


class PDFProcessor(BaseProcessor):
    """Uses normal text/table extraction per page, and only falls back to OCR
    on pages that yield little or no extractable text (i.e. scanned pages)."""

    def process(self, file_path: str) -> ProcessingResult:
        units: list[RawContentUnit] = []
        used_ocr = False

        with pdfplumber.open(file_path) as pdf:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()

                if len(text) < MIN_CHARS_BEFORE_OCR:
                    # Likely a scanned page - render and OCR it instead.
                    fitz_page = doc[page_num - 1]
                    pix = fitz_page.get_pixmap(dpi=200)
                    ocr_text = ocr_image_bytes(pix.tobytes("png"))
                    if ocr_text.strip():
                        used_ocr = True
                        units.append(RawContentUnit(
                            content_type="text",
                            text=ocr_text,
                            table_data=None,
                            location={"page": page_num},
                            metadata={"source": "ocr"},
                        ))
                elif text:
                    units.append(RawContentUnit(
                        content_type="text",
                        text=text,
                        table_data=None,
                        location={"page": page_num},
                        metadata={"source": "text"},
                    ))

                for t_idx, table in enumerate(page.extract_tables() or []):
                    if not table or len(table) < 2:
                        continue
                    headers = [str(h or "").strip() for h in table[0]]
                    rows = [[str(c or "").strip() for c in row] for row in table[1:]]
                    units.append(RawContentUnit(
                        content_type="table",
                        text=None,
                        table_data={"headers": headers, "rows": rows},
                        location={"page": page_num, "table": t_idx + 1},
                        metadata={},
                    ))
            doc.close()

        return ProcessingResult(content_units=units, used_ocr=used_ocr, document_content_type="application/pdf")
