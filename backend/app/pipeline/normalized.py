"""The normalized representation every document processor produces.

Instead of the rest of the pipeline branching on file type everywhere,
every processor (PDF, DOCX, TXT, CSV, XLSX, JSON, image) converts its
input into a `NormalizedDocument` — a flat list of `ContentUnit`s, each
carrying its own text/table content and a `Location` describing exactly
where in the source document it came from. Nothing downstream needs to
know what a "page" or a "row" is unless it's rendering one.
"""
from dataclasses import dataclass, field


@dataclass
class Location:
    """A flexible provenance pointer. Only the applicable fields are set —
    a DOCX chunk sets section/paragraph, an XLSX chunk sets sheet/row/column,
    a PDF chunk sets page, etc. Never fabricate a field that doesn't apply.
    """
    page: int | None = None
    section: str | None = None
    paragraph: int | None = None
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    table: str | None = None
    image: str | None = None
    region: list[float] | None = None   # [x1, y1, x2, y2]
    line: int | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def label(self) -> str:
        """Human-readable citation, e.g. 'Page 17' or 'Sheet Financials, Row 18, Column Revenue'."""
        parts = []
        if self.page is not None:
            parts.append(f"Page {self.page}")
        if self.sheet is not None:
            parts.append(f"Sheet {self.sheet}")
        if self.row is not None:
            parts.append(f"Row {self.row}")
        if self.column is not None:
            parts.append(f"Column {self.column}")
        if self.section is not None:
            parts.append(self.section)
        if self.paragraph is not None:
            parts.append(f"Paragraph {self.paragraph}")
        if self.table is not None:
            parts.append(f"Table {self.table}")
        if self.line is not None:
            parts.append(f"Line {self.line}")
        if self.image is not None:
            parts.append(f"Image {self.image}")
        return ", ".join(parts) if parts else "Document"

    @staticmethod
    def from_dict(d: dict | None) -> "Location":
        if not d:
            return Location()
        return Location(**{k: v for k, v in d.items() if k in Location.__dataclass_fields__})


@dataclass
class ContentUnit:
    """One retrievable/extractable slice of a document."""
    location: Location
    text: str = ""
    tables: list = field(default_factory=list)   # list of {headers, rows, name}
    content_type: str = "text"                    # "text" | "table" | "scanned" | "mixed"
    ocr_confidence: float | None = None
    notes: str = ""


@dataclass
class NormalizedDocument:
    """What every processor produces, regardless of source file type."""
    units: list[ContentUnit] = field(default_factory=list)
    unit_count_label: str = "pages"   # used for display, e.g. "7 pages" vs "3 sheets"

    def full_text(self) -> str:
        return "\n".join(u.text for u in self.units if u.text)

    def as_page_tuples(self) -> list[tuple[int, str]]:
        """Back-compat helper for pipeline code that wants (index, text) pairs."""
        return [(i + 1, u.text) for i, u in enumerate(self.units)]
