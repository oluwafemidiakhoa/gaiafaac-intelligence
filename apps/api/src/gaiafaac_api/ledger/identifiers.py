from __future__ import annotations

import re
from datetime import date, datetime
from enum import StrEnum


class GaiaObjectType(StrEnum):
    FAAC = "FAAC"
    IGR = "IGR"
    DEBT = "DEBT"
    DEBT_SERVICE = "DEBTSVC"
    BUDGET = "BUDGET"
    EXPENDITURE = "EXP"
    LIABILITY = "LIABILITY"
    CERTIFICATE = "CERT"
    SCENARIO = "SCENARIO"


_JURISDICTION = re.compile(r"^[A-Z]{2}(?:-[A-Z0-9]{2,8})+$")
_PERIOD = re.compile(r"^[0-9]{4}(?:(?:-?(?:0[1-9]|1[0-2]))|Q[1-4]|H[12]|-YTD)?$")
_DIGEST = re.compile(r"^[a-fA-F0-9]{64}$")


def _jurisdiction(value: str) -> str:
    normalized = value.strip().upper()
    if not _JURISDICTION.fullmatch(normalized):
        raise ValueError("Jurisdiction must be a canonical code such as NG-LA.")
    return normalized


def _period(value: str) -> str:
    normalized = value.strip().upper()
    if not _PERIOD.fullmatch(normalized):
        raise ValueError("Fiscal period must be a supported year, month, quarter, half, or YTD.")
    return normalized.replace("-", "")


def _suffix(integrity_hash: str) -> str:
    if not _DIGEST.fullmatch(integrity_hash):
        raise ValueError("Integrity hash must be a 64-character SHA-256 value.")
    return integrity_hash[:6].upper()


def gaia_object_id(
    object_type: GaiaObjectType,
    *,
    jurisdiction: str,
    fiscal_period: str,
    integrity_hash: str,
) -> str:
    """Build an immutable, content-versioned Gaia fiscal object identifier."""

    return (
        f"GF-{object_type.value}-{_jurisdiction(jurisdiction)}-"
        f"{_period(fiscal_period)}-{_suffix(integrity_hash)}"
    )


def fiscal_state_id(
    *, jurisdiction: str, effective_at: date | datetime, integrity_hash: str
) -> str:
    return f"GFS-{_jurisdiction(jurisdiction)}-{effective_at:%Y%m%d}-{_suffix(integrity_hash)}"
