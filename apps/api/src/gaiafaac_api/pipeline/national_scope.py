from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ExtractionStatus
from gaiafaac_api.database.models import ExtractionRun
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.national_distribution import validate_national_distribution

STATES_SCOPES = {"states_only_36", "states_plus_fct_37"}


def declare_national_states_scope(
    session: Session, *, run_id: uuid.UUID, states_scope: str
) -> None:
    """Declare the exact jurisdiction basis used by an official states aggregate.

    GaiaFAAC never guesses whether an official "states" figure includes the FCT. The
    operator must declare the source semantics before cross-source reconciliation can
    be published. Revalidation runs immediately so the declaration remains part of the
    governed extraction record.
    """
    scope = states_scope.strip().casefold()
    if scope not in STATES_SCOPES:
        raise ImportContractError(
            "states_scope must be states_only_36 or states_plus_fct_37"
        )
    run = session.get(ExtractionRun, run_id)
    if run is None:
        raise ImportContractError("Extraction run does not exist")
    configuration = dict(run.configuration or {})
    if configuration.get("scope") != "national_distribution":
        raise ImportContractError("Extraction run is not a national-distribution run")
    if run.status is not ExtractionStatus.REQUIRES_REVIEW:
        raise ImportContractError(
            "National states scope can only be declared while evidence is awaiting review"
        )
    configuration["states_scope"] = scope
    run.configuration = configuration
    validate_national_distribution(session, run)
    session.commit()
