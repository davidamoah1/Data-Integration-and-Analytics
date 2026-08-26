"""Custom exceptions for the platform.

These are caught by FastAPI exception handlers and converted to
standard JSON responses.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    """Raised when user lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppException):
    """Raised when a resource already exists."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AccountLockedError(AppException):
    """Raised when account is locked due to too many failed attempts."""

    def __init__(self, detail: str = "Account is locked due to too many failed login attempts"):
        super().__init__(detail=detail, status_code=status.HTTP_423_LOCKED)
