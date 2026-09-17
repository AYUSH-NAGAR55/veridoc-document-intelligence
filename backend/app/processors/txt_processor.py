"""Plain text processor. Groups content into paragraph-like blocks
separated by blank lines, tracking the starting line number of each
block for provenance ("Line 42").
"""
from .base import DocumentProcessor
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class TXTProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        units = []
        buffer, start_line = [], None
        for i, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip("\n")
            if line.strip():
                if start_line is None:
                    start_line = i
                buffer.append(line)
            else:
                if buffer:
                    units.append(ContentUnit(
                        location=Location(line=start_line),
                        text="\n".join(buffer),
                        content_type="text",
                    ))
                    buffer, start_line = [], None
        if buffer:
            units.append(ContentUnit(location=Location(line=start_line), text="\n".join(buffer)))

        return NormalizedDocument(units=units, unit_count_label="blocks")
