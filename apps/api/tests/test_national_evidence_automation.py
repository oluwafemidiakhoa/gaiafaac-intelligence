from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import NationalDistribution, ReportingPeriod, SourceDocument
from gaiafaac_api.database.national_evidence_models import NationalEvidenceCandidate
from gaiafaac_api.pipeline.national_evidence import FetchResponse, _official_url
from gaiafaac_api.pipeline.national_evidence_hardened import (
    NationalEvidenceError,
    extract_national_claims,
    run_national_evidence_collection,
)

ARTICLE_URL = (
    "https://fmino.gov.ng/fg-states-lgcs-share-n1-678-trillion-"
    "from-a-gross-total-of-n2-344-trillion-for-the-month-of-february-2025/"
)

ARTICLE_HTML = """
<html>
<head><title>FG, States, LGCs Share N1.678 Trillion From February 2025 Revenue | FAAC</title></head>
<body>
<article>
<time datetime="2025-03-22T10:30:00+01:00">March 22, 2025</time>
<p>At the March 2025 FAAC meeting, the Federation Account Allocation Committee
shared a total sum of N1.678 trillion as February 2025 federation revenue.</p>
<p>The Federal Government received N569.656 billion, the States received
N562.195 billion, and the Local Government Councils received N410.559 billion.</p>
<p>A total sum of N136.042 billion was shared to oil producing states as 13%
derivation revenue.</p>
</article>
</body>
</html>
"""

SEPTEMBER_2024_HTML = """
<html>
<head><title>FAAC: FG, STATES, LGCs SHARE N1.203 TRILLION FROM AUGUST 2024 REVENUE</title></head>
<body><article>
<p>At the September 2024 FAAC meeting, the Federation Account Allocation Committee
shared a total sum of N1.203 trillion as August 2024 federation revenue.</p>
<p>The Federal Government received N374.925 billion, the State Governments received
N422.861 billion and the Local Government Councils received N306.533 billion.</p>
<p>N99.474 billion was shared to the relevant States as 13% derivation revenue.</p>
</article></body></html>
"""

JULY_2024_UNIT_CONFLICT_HTML = """
<html>
<head><title>FAAC: FG, STATES, LGCs SHARE N1,358.075 TRILLION FOR JULY 2024</title></head>
<body><article>
<p>At the August 2024 FAAC meeting, FAAC shared N1,358.075 trillion as July 2024 revenue.</p>
<p>The Federal Government received N431.079 billion, the States received N473.477 billion
and the Local Government Councils received N343.703 billion.</p>
<p>N109.816 billion was shared to oil producing States as 13% derivation revenue.</p>
</article></body></html>
"""

SEPTEMBER_2024_SOURCE_CONFLICT_HTML = """
<html>
<head><title>FAAC: FG, STATES, LGCs SHARE N1.289 TRILLION FROM SEPTEMBER 2024 REVENUE</title></head>
<body><article>
<p>At the October 2024 FAAC meeting, FAAC shared a total sum of N1.298 trillion
as September 2024 federation revenue.</p>
<p>The Federal Government received N424.867 billion, the States received N453.724 billion
and the Local Government Councils received N329.864 billion.</p>
<p>N90.415 billion was shared to the relevant States as 13% derivation revenue.</p>
</article></body></html>
"""

SEARCH_HTML = f"""
<html><body><a href="{ARTICLE_URL}">FG States LGCs share FAAC revenue</a></body></html>
"""


def test_extracts_mixed_units_without_using_headline_recipient_mentions() -> None:
    claims = extract_national_claims(ARTICLE_HTML)
    assert claims.net_distributable_amount.normalized_billion == "1678"
    assert claims.federal_amount.normalized_billion == "569.656"
    assert claims.states_amount.normalized_billion == "562.195"
    assert claims.local_governments_amount.normalized_billion == "410.559"
    assert claims.derivation_amount.normalized_billion == "136.042"
    assert claims.disbursement_month == date(2025, 3, 1)
    assert claims.allocation_period_month == date(2025, 2, 1)


def test_realistic_2024_headline_does_not_poison_states_or_lgcs() -> None:
    claims = extract_national_claims(SEPTEMBER_2024_HTML)
    assert claims.net_distributable_amount.normalized_billion == "1203"
    assert claims.federal_amount.normalized_billion == "374.925"
    assert claims.states_amount.normalized_billion == "422.861"
    assert claims.local_governments_amount.normalized_billion == "306.533"
    assert claims.derivation_amount.normalized_billion == "99.474"


def test_orders_of_magnitude_source_unit_conflict_is_quarantinable() -> None:
    with pytest.raises(NationalEvidenceError) as caught:
        extract_national_claims(JULY_2024_UNIT_CONFLICT_HTML)
    assert caught.value.reason_code == "SOURCE_MONETARY_UNIT_CONFLICT"


def test_title_body_distributable_total_conflict_is_quarantinable() -> None:
    with pytest.raises(NationalEvidenceError) as caught:
        extract_national_claims(SEPTEMBER_2024_SOURCE_CONFLICT_HTML)
    assert caught.value.reason_code == "SOURCE_DISTRIBUTABLE_TOTAL_CONFLICT"


def test_official_url_guard_rejects_cross_domain_urls() -> None:
    assert _official_url(ARTICLE_URL, "fmino.gov.ng") == ARTICLE_URL
    try:
        _official_url("https://example.com/fake-faac", "fmino.gov.ng")
    except Exception as error:
        assert "Refusing non-official URL" in str(error)
    else:
        raise AssertionError("cross-domain source should be rejected")


class _FakeFetcher:
    def __call__(self, url: str, *, allowed_host: str) -> FetchResponse:
        if "?s=FAAC" in url and "paged=" not in url:
            body = SEARCH_HTML.encode()
        elif "paged=" in url:
            body = b"<html><body>No more results</body></html>"
        elif url == ARTICLE_URL:
            body = ARTICLE_HTML.encode()
        else:
            body = b"<html><body>No results</body></html>"
        return FetchResponse(body=body, content_type="text/html", final_url=url)


def test_collection_archives_imports_and_hardens_period_semantics(session: Session) -> None:
    period = ReportingPeriod(
        revenue_month=date(2025, 3, 1),
        reporting_label="OAGF FAAC Disbursement - March 2025 (Table III: state distribution)",
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.commit()

    summary = run_national_evidence_collection(
        session,
        months_back=36,
        fetcher=_FakeFetcher(),
        max_pages=2,
    )

    assert len(summary.queued) == 1
    assert summary.queued[0].blocking_finding_count == 0
    session.refresh(period)
    assert period.disbursement_month == date(2025, 3, 1)
    assert period.allocation_period_month == date(2025, 2, 1)

    candidate = session.scalar(select(NationalEvidenceCandidate))
    assert candidate is not None
    assert candidate.content == ARTICLE_HTML.encode()
    assert candidate.status == "imported"
    assert candidate.details["parser_version"] == "3"

    source = session.get(SourceDocument, candidate.source_document_id)
    assert source is not None
    assert source.sha256 == candidate.sha256
    assert source.storage_path == f"db://national-evidence-candidates/{candidate.id}"

    assert session.scalar(select(func.count(NationalDistribution.id))) == 1


def test_collection_is_idempotent_for_same_official_bytes(session: Session) -> None:
    session.add(
        ReportingPeriod(
            revenue_month=date(2025, 3, 1),
            reporting_label="March 2025 governed state allocations",
            verification_status=VerificationStatus.HUMAN_VERIFIED,
            is_demo=False,
            is_published=True,
        )
    )
    session.commit()

    first = run_national_evidence_collection(
        session,
        months_back=36,
        fetcher=_FakeFetcher(),
        max_pages=2,
    )
    second = run_national_evidence_collection(
        session,
        months_back=36,
        fetcher=_FakeFetcher(),
        max_pages=2,
    )

    assert len(first.queued) == 1
    assert len(second.queued) == 0
    assert ARTICLE_URL in second.duplicates
    assert session.scalar(select(func.count(NationalDistribution.id))) == 1
    assert session.scalar(select(func.count(NationalEvidenceCandidate.id))) == 1
