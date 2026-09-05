from __future__ import annotations

from sqlalchemy.orm import Session

from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystResponse
from gaiafaac_api.services.gaia_analyst_institutional import gaia_analyst as institutional_gaia_analyst


def gaia_analyst(session: Session, *, question: str, year: int) -> GaiaAnalystResponse:
    """Apply publication/source semantics shared by the public Ask Gaia surface.

    The underlying IGR services resolve from the canonical FiscalClaim ledger. This
    wrapper makes the source scope visible in the natural-language answer and makes
    the Year control semantics explicit for latest-versus-year-specific questions.
    """

    result = institutional_gaia_analyst(session, question=question, year=year)
    igr_evidence = [item for item in result.evidence if item.evidence_domain == "igr"]
    if not igr_evidence:
        return result

    sources = sorted(
        {
            item.source_organization.strip()
            for item in igr_evidence
            if item.source_organization and item.source_organization.strip()
        }
    )
    source_text = ", ".join(sources) if sources else "the cited governed source"
    answer = result.answer.rstrip()
    if answer.endswith("."):
        answer = answer[:-1]
    answer = f"{answer}. Source: {source_text}."

    if result.intent == "igr_latest":
        caveat = (
            "This is a latest-publication query: the Year control is not used to restrict the "
            "search. Gaia searches the latest current, verified IGR publication in the canonical "
            "FiscalClaim ledger for the named jurisdiction."
        )
    else:
        caveat = (
            f"This is a year-specific IGR query: the Year control restricts the search to {year}. "
            "Only current, verified IGR publications in the canonical FiscalClaim ledger are used."
        )

    return result.model_copy(update={"answer": answer, "caveat": caveat})
