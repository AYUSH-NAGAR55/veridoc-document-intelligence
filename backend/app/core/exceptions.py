class VeriDocError(Exception):
    """Base class for expected, user-facing errors. Anything else (unexpected
    exceptions) gets logged server-side and returned as a generic 500 - the
    user never sees a raw stack trace."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFound(VeriDocError):
    def __init__(self, document_id: str):
        super().__init__(f"Document '{document_id}' was not found.", status_code=404)


class ProcessingError(VeriDocError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
