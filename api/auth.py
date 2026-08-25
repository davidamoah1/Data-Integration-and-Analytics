"""API key authentication for FastAPI endpoints.

Supports API key passed via X-API-Key header or ?api_key query parameter.
The valid API key is loaded from the API_KEY environment variable.
"""

import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

_DEV_KEY = "dev-api-key-change-in-production"


def _get_valid_api_key() -> str:
    """Get the valid API key from environment.

    In production (DB_TYPE=mysql or APP_ENV=production), the default dev key is rejected.
    """
    key = os.getenv("API_KEY", _DEV_KEY)
    is_prod = os.getenv("DB_TYPE", "").lower() == "mysql" or os.getenv(
        "APP_ENV", ""
    ).lower() == "production"
    if is_prod and key == _DEV_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY environment variable must be set in production.",
        )
    return key


def get_api_key(
    header_key: str = Security(api_key_header),
    query_key: str = Security(api_key_query),
) -> str:
    """Validate the API key from header or query parameter.

    Args:
        header_key: API key from X-API-Key header.
        query_key: API key from ?api_key query parameter.

    Returns:
        The validated API key.

    Raises:
        HTTPException: 401 if no valid API key is provided.
    """
    valid_key = _get_valid_api_key()
    provided_key = header_key or query_key

    if provided_key and secrets.compare_digest(provided_key, valid_key):
        return provided_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key. Provide via X-API-Key header or ?api_key query parameter.",
        headers={"WWW-Authenticate": "ApiKey"},
    )
