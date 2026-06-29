from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def new_id(prefix: str) -> str:
    """Create a compact, stable string identifier for a ledger object."""

    cleaned = prefix.strip().lower().replace("_", "-") or "id"
    return f"{cleaned}-{uuid4().hex[:16]}"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return utc_now().isoformat()
