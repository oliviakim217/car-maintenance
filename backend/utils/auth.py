"""Session-based authentication dependency for FastAPI routes."""

from fastapi import HTTPException, Request, status


def require_session(request: Request) -> None:
    """Reject requests from unauthenticated sessions.

    Raises HTTP 401 if the session cookie does not contain an
    authenticated flag set by the /login endpoint.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
