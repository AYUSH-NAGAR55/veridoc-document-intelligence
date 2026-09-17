from dataclasses import dataclass, field


@dataclass
class RawContentUnit:
    content_type: str  # text | table | image_text
    text: str | None
    table_data: dict | None
    location: dict
    metadata: dict = field(default_factory=dict)


@dataclass
class ProcessingResult:
    content_units: list[RawContentUnit]
    used_ocr: bool = False
    document_content_type: str | None = None


class BaseProcessor:
    def process(self, file_path: str) -> ProcessingResult:
        raise NotImplementedError
