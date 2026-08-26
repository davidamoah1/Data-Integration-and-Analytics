"""Standard API response format for consistent API responses."""

from typing import Any

from pydantic import BaseModel


class StandardResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    message: str = "OK"
    data: Any | None = None
    errors: list[str] | None = None


def success_response(data: Any = None, message: str = "OK") -> dict:
    """Create a success response dict."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, errors: list[str] | None = None) -> dict:
    """Create an error response dict."""
    return {"success": False, "message": message, "errors": errors or []}
