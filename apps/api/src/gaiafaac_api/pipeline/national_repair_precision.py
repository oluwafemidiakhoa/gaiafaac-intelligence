from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ExtractionRun
from gaiafaac_api.database.national_evidence_models import NationalEvidenceCandidate
from gaiafaac_api.pipeline import national_evidence as legacy
from gaiafaac_api.pipeline.national_distribution import validate_national_distribution

_REQUIRED_CLAIMS = (
    "net_distributable_amount",
    "federal_amount",
    "states_amount",
    "local_governments_amount",
    "derivation_amount",
)


def _normalized_original_values(candidate: NationalEvidenceCandidate) -> dict[str, str]:
    extracted = candidate.extracted_claims
    if not isinstance(extracted, dict):
        raise ValueError("National evidence candidate has no extracted claims")

    values: dict[str, str] = {}
    for field_name in _REQUIRED_CLAIMS:
        raw_claim = extracted.get(field_name)
        if not isinstance(raw_claim, dict):
            raise ValueError(f"National evidence candidate is missing {field_name}")
        normalized = raw_claim.get("normalized_billion")
        if normalized is None:
            raise ValueError(
                f"National evidence candidate has no normalized value for {field_name}"
            )
        values[field_name] = str(normalized)
    return values


def revalidate_repaired_source_precision(
    session: Session,
    *,
    run_ids: set[uuid.UUID],
) -> list[str]:
    """Restore the source-precision basis for repaired, still-active national packets.

    The national validator interprets ``original_values`` in the distribution's reported unit.
    Autopilot imports use billion-naira normalized numeric strings there. The first repair pass
    accidentally replaced those strings with full source phrases (for example ``N1.203 trillion``),
    which the precision parser cannot interpret and therefore collapses tolerance to one kobo.

    Keep the literal source phrases in ``candidate.extracted_claims`` for provenance, while restoring
    the normalized billion-naira strings used by the validator for precision-aware reconciliation.
    """
    updated: list[str] = []
    for run_id in run_ids:
        run = session.get(ExtractionRun, run_id)
        if run is None:
            continue
        candidate = session.scalar(
            select(NationalEvidenceCandidate).where(
                NationalEvidenceCandidate.extraction_run_id == run_id
            )
        )
        if candidate is None or candidate.status != legacy.STATUS_IMPORTED:
            continue

        configuration = dict(run.configuration or {})
        originals = dict(configuration.get("original_values") or {})
        originals.update(_normalized_original_values(candidate))
        configuration["original_values"] = originals
        configuration["precision_basis"] = "normalized_billion_display_values"
        run.configuration = configuration

        validate_national_distribution(session, run)
        updated.append(str(run.id))

    session.commit()
    return updated
