from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from gaiafaac_api.ledger import (
    EvidenceIntegrityConfig,
    calculate_evidence_coverage,
    calculate_evidence_integrity,
)


def test_coverage_uses_documented_equal_domain_weights() -> None:
    domains = {
        "faac": {"status": "verified"},
        "igr": {"status": "verified"},
        "debt": {"status": "partial"},
        "debt_service": {"status": "unavailable"},
        "budget": {"status": "verified"},
        "expenditure": {"status": "partial"},
        "liabilities": {"status": "unavailable"},
    }

    result = calculate_evidence_coverage(domains)

    assert result["score"] == "0.5714"
    assert result["percent"] == "57.14"
    assert result["status"] == "calculated"
    assert result["domain_weights"]["debt"] == "0.5"
    assert result["domain_weights"]["liabilities"] == "0"


def test_integrity_reports_missing_components_instead_of_inventing_scores() -> None:
    coverage = calculate_evidence_coverage(
        {"faac": {"status": "unavailable"}, "igr": {"status": "unavailable"}}
    )

    result = calculate_evidence_integrity(
        claims=[],
        verifications=[],
        domains={},
        coverage=coverage,
        sources=[],
        unresolved_conflict_count=0,
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
    )

    assert result["score"] is None
    assert result["status"] == "insufficient_evidence"
    assert result["components"]["source_authenticity"]["score"] is None
    assert result["components"]["domain_completeness"]["score"] == "0.00"


def test_integrity_config_requires_exact_reproducible_weights() -> None:
    with pytest.raises(ValueError, match="sum exactly"):
        EvidenceIntegrityConfig(source_authenticity_weight=Decimal("0.21"))


def test_integrity_uses_exact_decimal_components_and_conflict_penalty() -> None:
    coverage = calculate_evidence_coverage(
        {
            "faac": {"status": "verified"},
            "igr": {"status": "unavailable"},
            "debt": {"status": "unavailable"},
            "debt_service": {"status": "unavailable"},
            "budget": {"status": "unavailable"},
            "expenditure": {"status": "unavailable"},
            "liabilities": {"status": "unavailable"},
        }
    )
    claim = SimpleNamespace(object_type="faac", fiscal_period="2026-06")
    verification = SimpleNamespace(source_verified=True, reconciled=True, human_reviewed=True)
    sources = [
        {"publisher": "Agency A", "publication_date": "2026-08-01"},
        {"publisher": "Agency B", "publication_date": "2026-08-01"},
    ]

    agreed = calculate_evidence_integrity(
        claims=[claim],
        verifications=[verification],
        domains={},
        coverage=coverage,
        sources=sources,
        unresolved_conflict_count=0,
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    conflicting = calculate_evidence_integrity(
        claims=[claim],
        verifications=[verification],
        domains={},
        coverage=coverage,
        sources=sources,
        unresolved_conflict_count=1,
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
    )

    assert agreed["components"]["cross_source_agreement"]["score"] == "100.00"
    assert conflicting["components"]["cross_source_agreement"]["score"] == "0.00"
    assert Decimal(conflicting["score"]) < Decimal(agreed["score"])
