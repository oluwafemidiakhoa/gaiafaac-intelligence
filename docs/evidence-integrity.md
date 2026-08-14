# Gaia Evidence Integrity

Evidence Integrity is a deterministic measure of Gaia's evidence quality and
completeness. It is not a credit rating, fiscal-health score, default probability, or
assessment of misconduct. Phase 2 methodology is `gaia-evidence-integrity-v1`.

The configured component weights are:

| Component              | Weight | Deterministic input                                                                                      |
| ---------------------- | -----: | -------------------------------------------------------------------------------------------------------- |
| Source authenticity    |    20% | Share of included claims whose retained source is approved.                                              |
| Reconciliation         |    20% | Share of applicable claims whose exact gross-minus-deductions calculation reconciles.                    |
| Human verification     |    20% | Share of included claims with recorded human review.                                                     |
| Temporal completeness  |    10% | Distinct monthly FAAC periods divided by elapsed months in the state year, capped at 100%.               |
| Domain completeness    |    15% | The versioned Evidence Coverage result.                                                                  |
| Cross-source agreement |     5% | 100 with at least two publishers and no conflict; 0 with an unresolved conflict; otherwise insufficient. |
| Data freshness         |    10% | Mean linear freshness over a 90-day publication window.                                                  |

An overall score is calculated only when source authenticity, human verification,
and domain completeness are available and the available component weight is at least
75%. Available weights are renormalized; unavailable components are never converted
to zero. Component and overall arithmetic use `Decimal`.

Insufficient results remain explicit:

```json
{
  "score": null,
  "status": "insufficient_evidence",
  "methodology_version": "gaia-evidence-integrity-v1"
}
```

An unresolved, explicitly recorded source conflict produces zero only for the
cross-source-agreement component. It does not silently select either claim.
