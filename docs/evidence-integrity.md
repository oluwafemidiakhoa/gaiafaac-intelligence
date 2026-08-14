# Gaia Evidence Integrity

Evidence Integrity is a future deterministic measure of Gaia's evidence quality and
completeness. It is not a credit rating, fiscal-health score, default probability, or
assessment of misconduct.

Phase 1 provides the inputs and response shape but intentionally does not calculate a
score. Responses contain:

```json
{
  "score": null,
  "status": "insufficient_evidence",
  "methodology_version": "1.0.0"
}
```

Phase 2 must publish a versioned methodology for source authenticity,
reconciliation, human verification, temporal completeness, domain completeness,
cross-source agreement, and freshness before any score is exposed. Missing component
evidence must remain insufficient rather than becoming zero.
