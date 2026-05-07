"""API key authentication dependency for FastAPI routes."""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(_API_KEY_HEADER)) -> None:
    """Reject requests that do not carry the correct API key.

    The expected key is read from APP_API_KEY in the environment.
    Raises HTTP 401 if the key is missing or wrong.
    """
    expected = os.getenv("APP_API_KEY")
    if not expected:
        raise RuntimeError("APP_API_KEY is not set in the environment")
    if key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
