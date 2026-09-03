import pytest
from sqlalchemy.orm import Session

from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.errors import StateNormalizationError
from gaiafaac_api.pipeline.states import StateNormalizer


def test_state_normalizer_matches_canonical_values_and_curated_aliases(
    session: Session,
) -> None:
    seed_states(session)
    normalizer = StateNormalizer.from_session(session)

    assert normalizer.match("Lagos State").state.code == "LA"
    assert normalizer.match("cross-river").state.code == "CR"
    assert normalizer.match("F.C.T.").state.code == "FC"
    assert normalizer.match("Abuja").state.code == "FC"
    assert normalizer.match("Federal Capital Territory (FCT)").state.code == "FC"


def test_state_normalizer_rejects_fuzzy_or_unknown_values(session: Session) -> None:
    seed_states(session)
    normalizer = StateNormalizer.from_session(session)

    with pytest.raises(StateNormalizationError):
        normalizer.match("Laggoz")
    with pytest.raises(StateNormalizationError):
        normalizer.match("")
