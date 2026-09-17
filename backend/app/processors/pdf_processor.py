"""PDF processor. Wraps the existing, already-working classify + extract
logic (page type detection, table extraction, OCR-for-scanned-pages) and
adapts its output into the common NormalizedDocument shape.
"""
from .base import DocumentProcessor
from ..pipeline import classifier, extractor
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class PDFProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        assessments = classifier.classify_pdf(file_path)
        units = []
        for assessment in assessments:
            page_extraction = extractor.extract_page(file_path, assessment)
            tables = [
                {"name": f"Table {i + 1}", "rows": t}
                for i, t in enumerate(page_extraction.tables)
            ]
            units.append(ContentUnit(
                location=Location(page=assessment.page_number),
                text=page_extraction.text,
                tables=tables,
                content_type=assessment.page_type,
                ocr_confidence=page_extraction.ocr_confidence,
                notes=page_extraction.notes,
            ))
        return NormalizedDocument(units=units, unit_count_label="pages")
