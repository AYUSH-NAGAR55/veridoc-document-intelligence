"""JSON processor. Flattens arbitrarily nested JSON into individual
content units, each labeled with its key path (e.g. "invoice.items[2].price")
stored as the section, so provenance stays meaningful even though JSON
has no natural notion of a page or row.
"""
import json

from .base import DocumentProcessor
from ..pipeline.normalized import NormalizedDocument, ContentUnit, Location


class JSONProcessor(DocumentProcessor):
    def process(self, file_path: str) -> NormalizedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        units = []
        _flatten(data, path="$", units=units)

        # Also keep one unit with the whole document, pretty-printed, for
        # questions that need broader context than a single leaf value.
        units.append(ContentUnit(
            location=Location(section="Full document"),
            text=json.dumps(data, indent=2)[:4000],
            content_type="text",
        ))

        return NormalizedDocument(units=units, unit_count_label="fields")


def _flatten(value, path: str, units: list):
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(v, f"{path}.{k}", units)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _flatten(item, f"{path}[{i}]", units)
    else:
        if value is None or str(value).strip() == "":
            return
        units.append(ContentUnit(
            location=Location(section=path),
            text=f"{path}: {value}",
            content_type="text",
        ))
