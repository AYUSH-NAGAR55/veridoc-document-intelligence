from app.models.document import DocumentType
from app.services.processors.base import BaseProcessor
from app.services.processors.pdf_processor import PDFProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.simple_processors import TXTProcessor, CSVProcessor, JSONProcessor, ImageProcessor

_REGISTRY: dict[DocumentType, type[BaseProcessor]] = {
    DocumentType.PDF: PDFProcessor,
    DocumentType.DOCX: DOCXProcessor,
    DocumentType.TXT: TXTProcessor,
    DocumentType.CSV: CSVProcessor,
    DocumentType.JSON: JSONProcessor,
    DocumentType.IMAGE: ImageProcessor,
}


def get_processor(file_type: DocumentType) -> BaseProcessor:
    cls = _REGISTRY.get(file_type)
    if not cls:
        raise ValueError(f"No processor registered for file type: {file_type}")
    return cls()
