"""
interfaces/plumbing.py — the three lines of WSGI that are easy to get subtly wrong.

Kept apart from the routing so `http.py` stays a list of decisions rather than a
list of string handling.
"""

from __future__ import annotations

import json


def cookie(environ, name: str) -> str | None:
    for part in (environ.get("HTTP_COOKIE") or "").split(";"):
        if "=" in part:
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
    return None


def ip(environ) -> str:
    """Behind Render the client address is in X-Forwarded-For; trust the first hop."""
    fwd = (environ.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return fwd or environ.get("REMOTE_ADDR") or "unknown"


def raw_body(environ, limit: int = 65536) -> bytes:
    """The exact bytes received. A webhook signature is over these, not over JSON."""
    try:
        n = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return b""
    if n <= 0:
        return b""
    return environ["wsgi.input"].read(min(n, limit))


def json_body(environ) -> dict:
    try:
        parsed = json.loads(raw_body(environ).decode() or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}
