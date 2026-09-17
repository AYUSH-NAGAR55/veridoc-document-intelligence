"""CSV processor. Keeps the header row and produces one ContentUnit per
data row (so a question about "row 18" resolves precisely), plus a
single table-shaped unit holding the whole sheet for broader retrieval.
"""
import csv

from .base import DocumentProcessor
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class CSVProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return NormalizedDocument(units=[], unit_count_label="rows")

        headers = rows[0]
        data_rows = rows[1:]
        units = []

        for row_idx, row in enumerate(data_rows, start=2):  # row 1 is the header
            row_dict = dict(zip(headers, row))
            text = "; ".join(f"{h}: {v}" for h, v in row_dict.items() if h)
            # One column-anchored unit per non-empty cell so a specific
            # "column X" question can cite precisely.
            for col_idx, header in enumerate(headers):
                value = row[col_idx] if col_idx < len(row) else ""
                if not value.strip():
                    continue
                units.append(ContentUnit(
                    location=Location(row=row_idx, column=header),
                    text=f"{header}: {value} (row {row_idx})",
                    content_type="table",
                ))

        units.append(ContentUnit(
            location=Location(table="Full sheet"),
            text="\n".join(", ".join(r) for r in rows),
            tables=[{"name": "Full sheet", "rows": rows}],
            content_type="table",
        ))

        return NormalizedDocument(units=units, unit_count_label="rows")
