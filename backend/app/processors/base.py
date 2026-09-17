"""Base interface every format-specific processor implements, plus the
registry that picks the right one by file extension.

Adding a new supported format means writing one class here and
registering it — nothing else in the pipeline needs to change, since
everything downstream works off `NormalizedDocument`.
"""
import os
from abc import ABC, abstractmethod

from ..pipeline.normalized import NormalizedDocument


class DocumentProcessor(ABC):
    """One processor per file type. Must produce a NormalizedDocument."""

    @abstractmethod
    def process(self, file_path: str) -> NormalizedDocument:
        ...


class UnsupportedFormatError(Exception):
    def __init__(self, extension: str):
        self.extension = extension
        super().__init__(f"'{extension}' files aren't supported yet.")


def get_processor(file_path: str) -> DocumentProcessor:
    # Imported lazily to avoid circular imports and to keep heavy libraries
    # (docx, openpyxl, cv2) out of the import path until actually needed.
    from .pdf_processor import PDFProcessor
    from .docx_processor import DOCXProcessor
    from .txt_processor import TXTProcessor
    from .csv_processor import CSVProcessor
    from .xlsx_processor import XLSXProcessor
    from .json_processor import JSONProcessor
    from .image_processor import ImageProcessor

    ext = os.path.splitext(file_path)[1].lower()
    registry = {
        ".pdf": PDFProcessor,
        ".docx": DOCXProcessor,
        ".txt": TXTProcessor,
        ".csv": CSVProcessor,
        ".xlsx": XLSXProcessor,
        ".xls": XLSXProcessor,
        ".json": JSONProcessor,
        ".png": ImageProcessor,
        ".jpg": ImageProcessor,
        ".jpeg": ImageProcessor,
    }
    cls = registry.get(ext)
    if cls is None:
        raise UnsupportedFormatError(ext)
    return cls()
