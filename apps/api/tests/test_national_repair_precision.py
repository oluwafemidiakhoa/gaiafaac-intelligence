from types import SimpleNamespace

from gaiafaac_api.pipeline.national_repair_precision import _normalized_original_values


def test_repair_precision_uses_normalized_billion_values_not_source_phrases() -> None:
    candidate = SimpleNamespace(
        extracted_claims={
            "net_distributable_amount": {
                "original": "shared a total sum of N1.203 trillion",
                "normalized_billion": "1203",
            },
            "federal_amount": {
                "original": "Federal Government received N374.925 billion",
                "normalized_billion": "374.925",
            },
            "states_amount": {
                "original": "State Governments received N422.861 billion",
                "normalized_billion": "422.861",
            },
            "local_governments_amount": {
                "original": "Local Government Councils received N306.533 billion",
                "normalized_billion": "306.533",
            },
            "derivation_amount": {
                "original": "N99.474 billion was shared as 13% derivation revenue",
                "normalized_billion": "99.474",
            },
        }
    )

    originals = _normalized_original_values(candidate)  # type: ignore[arg-type]

    assert originals == {
        "net_distributable_amount": "1203",
        "federal_amount": "374.925",
        "states_amount": "422.861",
        "local_governments_amount": "306.533",
        "derivation_amount": "99.474",
    }
