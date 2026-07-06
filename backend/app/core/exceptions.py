from fastapi import HTTPException, status


class AppError(HTTPException):
    """Typed HTTP error used by services to return clean API failures."""

    def __init__(self, detail: str, code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=code, detail=detail)

