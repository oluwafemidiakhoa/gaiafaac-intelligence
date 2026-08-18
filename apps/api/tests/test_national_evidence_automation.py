from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import NationalDistribution, ReportingPeriod, SourceDocument
from gaiafaac_api.database.national_evidence_models import NationalEvidenceCandidate
from gaiafaac_api.pipeline.national_evidence import (
    FetchResponse,
    NationalEvidenceError,
    _official_url,
    extract_national_claims,
    run_national_evidence_collection,
)

ARTICLE_URL = (
    "https://fmino.gov.ng/fg-states-lgcs-share-n1-678-trillion-"
    "from-a-gross-total-of-n2-344-trillion-for-the-month-of-february-2025/"
)

ARTICLE_HTML = f"""
<html>
<head><title>FG, States, LGCs Share N1.678 Trillion From February 2025 Revenue</title></head>
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

SEARCH_HTML = f"""
<html><body><a href="{ARTICLE_URL}">FG States LGCs share FAAC revenue</a></body></html>
"""


def test_extracts_mixed_units_without_using_title_amounts() -> None:
    claims = extract_national_claims(ARTICLE_HTML)
    assert claims.net_distributable_amount.normalized_billion == "1678"
    assert claims.federal_amount.normalized_billion == "569.656"
    assert claims.states_amount.normalized_billion == "562.195"
    assert claims.local_governments_amount.normalized_billion == "410.559"
    assert claims.derivation_amount.normalized_billion == "136.042"
    assert claims.disbursement_month == date(2025, 3, 1)
    assert claims.allocation_period_month == date(2025, 2, 1)


def test_official_url_guard_rejects_cross_domain_urls() -> None:
    assert _official_url(ARTICLE_URL, "fmino.gov.ng") == ARTICLE_URL
    try:
        _official_url("https://example.com/fake-faac", "fmino.gov.ng")
    except NationalEvidenceError as error:
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
