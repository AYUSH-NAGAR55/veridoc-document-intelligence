"""DOCX processor. Walks paragraphs in document order, tracking the most
recent heading as the "section" label so provenance reads naturally
(e.g. "Financial Summary, Paragraph 12"), and extracts tables separately
with row/column structure preserved.
"""
import docx

from .base import DocumentProcessor
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class DOCXProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        document = docx.Document(file_path)
        units = []
        current_section = None
        para_index = 0

        for para in document.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            para_index += 1
            if para.style and para.style.name and para.style.name.lower().startswith("heading"):
                current_section = text
            units.append(ContentUnit(
                location=Location(section=current_section, paragraph=para_index),
                text=text,
                content_type="text",
            ))

        for t_idx, table in enumerate(document.tables):
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            table_name = f"Table {t_idx + 1}"
            units.append(ContentUnit(
                location=Location(section=current_section, table=table_name),
                text=_table_to_text(rows),
                tables=[{"name": table_name, "rows": rows}],
                content_type="table",
            ))

        return NormalizedDocument(units=units, unit_count_label="paragraphs")


def _table_to_text(rows: list) -> str:
    return "\n".join(" | ".join(row) for row in rows)
