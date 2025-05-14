from fastapi.responses import JSONResponse

class Error:
    """
    Represents an API error response with standardized formatting.

    This class encapsulates error details including error code and message,
    and provides methods to convert the error to different formats.
    """

    def __init__(self, code: int, message: str):
        if not isinstance(code, int):
            raise TypeError(f"Status code must be an integer, got {type(code).__name__}")
        if not 100 <= code <= 599:
            raise ValueError(f"Invalid HTTP status code: {code}. Code must be between 100 and 599")
        self.code = code
        self.message = message

    def to_dict(self):
        return {"code": self.code, "message": self.message}

    def to_response(self):
        return JSONResponse(status_code=self.code, content=self.to_dict())

    def __call__(self):
        return self.to_response()

class PncException(Exception):
    """Base exception for application-specific errors."""

    def __init__(self, message: str, status_code: int = 500):
        if not 100 <= status_code <= 599:
            raise ValueError(f"Invalid HTTP status code: {status_code}. Code must be between 100 and 599")
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OcrException(PncException):
    """Exception raised for OCR-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


class ClassificationException(PncException):
    """Exception raised for classification-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


class VolumeException(PncException):
    """Exception raised for volume-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)

