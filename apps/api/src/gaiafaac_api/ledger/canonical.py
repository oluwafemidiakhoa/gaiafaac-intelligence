from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

CANONICALIZATION_VERSION = "gaia-canonical-json-v1"


def _text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonicalize(value: Any) -> Any:
    """Convert supported domain values to stable, JSON-compatible values.

    Decimal scale is preserved as a string, timezone-aware datetimes are
    normalized to UTC, and binary floating point is rejected deliberately.
    Lists retain their semantic order; callers must sort unordered domain
    collections before hashing.
    """

    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        raise TypeError("Binary floating-point values are not canonical fiscal values.")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Non-finite Decimal values cannot be canonicalized.")
        return format(value, "f")
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Canonical datetimes must be timezone-aware.")
        return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return canonicalize(value.value)
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Canonical object keys must be strings.")
            normalized_key = _text(key)
            if normalized_key in normalized:
                raise ValueError("Unicode normalization produced a duplicate object key.")
            normalized[normalized_key] = canonicalize(item)
        return normalized
    if isinstance(value, list | tuple):
        return [canonicalize(item) for item in value]
    raise TypeError(f"Unsupported canonical value type: {type(value).__name__}.")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
