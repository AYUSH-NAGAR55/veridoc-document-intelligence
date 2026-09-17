import json

import pandas as pd

from app.services.processors.base import BaseProcessor, ProcessingResult, RawContentUnit
from app.services.ocr_service import ocr_image_file


class TXTProcessor(BaseProcessor):
    def process(self, file_path: str) -> ProcessingResult:
        units: list[RawContentUnit] = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Group consecutive lines into small blocks so we don't create a chunk per line,
        # but still keep an exact starting line number for provenance.
        block, block_start = [], 1
        for i, line in enumerate(lines, start=1):
            if line.strip() == "" and block:
                units.append(RawContentUnit(
                    content_type="text", text="\n".join(block).strip(), table_data=None,
                    location={"line": block_start}, metadata={},
                ))
                block, block_start = [], i + 1
            elif line.strip():
                if not block:
                    block_start = i
                block.append(line.rstrip("\n"))
        if block:
            units.append(RawContentUnit(
                content_type="text", text="\n".join(block).strip(), table_data=None,
                location={"line": block_start}, metadata={},
            ))

        return ProcessingResult(content_units=units, used_ocr=False, document_content_type="text/plain")


class CSVProcessor(BaseProcessor):
    def process(self, file_path: str) -> ProcessingResult:
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        headers = list(df.columns)
        rows = df.values.tolist()

        units = [RawContentUnit(
            content_type="table",
            text=None,
            table_data={"headers": headers, "rows": rows},
            location={"sheet": "Sheet1", "rows": f"1-{len(rows)}"},
            metadata={},
        )]
        # Also emit a per-row text unit so RAG can retrieve individual rows precisely.
        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row_text = ", ".join(f"{h}: {v}" for h, v in zip(headers, row) if str(v).strip())
            if row_text:
                units.append(RawContentUnit(
                    content_type="text", text=row_text, table_data=None,
                    location={"sheet": "Sheet1", "row": i}, metadata={"row_index": i},
                ))
        return ProcessingResult(content_units=units, used_ocr=False, document_content_type="text/csv")


class JSONProcessor(BaseProcessor):
    def process(self, file_path: str) -> ProcessingResult:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        units: list[RawContentUnit] = []

        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")
            else:
                units.append(RawContentUnit(
                    content_type="text",
                    text=f"{path}: {node}",
                    table_data=None,
                    location={"json_path": path},
                    metadata={},
                ))

        walk(data, "")
        return ProcessingResult(content_units=units, used_ocr=False, document_content_type="application/json")


class ImageProcessor(BaseProcessor):
    def process(self, file_path: str) -> ProcessingResult:
        text = ocr_image_file(file_path)
        units = []
        if text.strip():
            units.append(RawContentUnit(
                content_type="image_text",
                text=text,
                table_data=None,
                location={"region": "full_image"},
                metadata={"source": "ocr"},
            ))
        return ProcessingResult(content_units=units, used_ocr=True, document_content_type="image")
