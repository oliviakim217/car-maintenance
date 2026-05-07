"""Authentication endpoints: login, logout, and session status check."""

import hmac
import logging
import os
import time

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from backend.utils.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=256)


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginBody) -> dict:
    """Verify password and create an authenticated session."""
    start_ms = time.monotonic()
    logger.info("BEGIN:login")
    try:
        expected = os.getenv("APP_PASSWORD")
        if not expected:
            raise RuntimeError("APP_PASSWORD is not set in the environment")
        if not hmac.compare_digest(body.password, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )
        request.session["authenticated"] = True
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"ERROR:login error={exc} duration_ms={int((time.monotonic() - start_ms) * 1000)}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        logger.info(f"END:login duration_ms={int((time.monotonic() - start_ms) * 1000)}")


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Clear the session."""
    request.session.clear()
    return {"status": "ok"}


@router.get("/api/status")
async def session_status(request: Request) -> dict:
    """Return 200 if the session is authenticated, 401 otherwise.

    Used by the frontend on page load to decide whether to show the
    login overlay or the dashboard.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {"status": "ok"}
