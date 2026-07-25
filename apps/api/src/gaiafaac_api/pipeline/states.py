from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import State
from gaiafaac_api.pipeline.errors import StateNormalizationError

_EXPLICIT_ALIASES = {
    "abuja": "FC",
    "f c t": "FC",
    "fct": "FC",
    "federal capital territory abuja": "FC",
    "akwaibom": "AK",
    "crossriver": "CR",
}


def normalize_state_key(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


@dataclass(frozen=True)
class StateMatch:
    state: State
    submitted_name: str
    normalized_key: str


class StateNormalizer:
    """Exact canonical and explicitly curated state matching; no fuzzy inference."""

    def __init__(self, states: list[State]) -> None:
        self._by_key: dict[str, State] = {}
        self._by_code = {state.code: state for state in states}
        for state in states:
            for value in (state.name, state.code, state.slug):
                self._by_key[normalize_state_key(value)] = state
        for alias, code in _EXPLICIT_ALIASES.items():
            if code in self._by_code:
                self._by_key[normalize_state_key(alias)] = self._by_code[code]

    @classmethod
    def from_session(cls, session: Session) -> StateNormalizer:
        return cls(list(session.scalars(select(State).order_by(State.code))))

    def match(self, submitted_name: str) -> StateMatch:
        key = normalize_state_key(submitted_name)
        if not key:
            raise StateNormalizationError("State name is blank")
        lookup_key = key.removesuffix(" state")
        try:
            state = self._by_key[lookup_key]
        except KeyError as error:
            raise StateNormalizationError(
                f"Unknown state name or unsupported alias: {submitted_name!r}"
            ) from error
        return StateMatch(state=state, submitted_name=submitted_name, normalized_key=key)
