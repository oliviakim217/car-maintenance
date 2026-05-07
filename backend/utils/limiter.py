"""Shared slowapi rate limiter instance."""

from slowapi import Limiter
from starlette.requests import Request


def _real_ip(request: Request) -> str:
    # Use the TCP connection IP only — cannot be spoofed via X-Forwarded-For
    return request.client.host


limiter = Limiter(key_func=_real_ip)
