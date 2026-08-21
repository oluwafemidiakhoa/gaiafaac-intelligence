from datetime import date

import pytest
from sqlalchemy import select

from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.dmo.archive import DmoDownload, archive_dmo_publication
from gaiafaac_api.pipeline.dmo.discovery import DmoPublicationCandidate


def _candidate() -> DmoPublicationCandidate:
    return DmoPublicationCandidate(
        title="States and FCT Domestic Debt Stock as at March 31, 2026",
        document_url=(
            "https://www.dmo.gov.ng/debt-profile/sub-national-debts/"
            "6001-states-and-fct-domestic-debt-stock-as-at-march-31-2026"
        ),
        debt_kind="domestic",
        as_of_date=date(2026, 3, 31),
    )


def test_archive_registers_immutable_pdf_source(session, tmp_path):
    body = b"%PDF-1.7\nfixture debt table\n%%EOF"

    result = archive_dmo_publication(
        session,
        _candidate(),
        archive_root=tmp_path,
        fetch=lambda _url: DmoDownload(
            body=body,
            content_type="application/pdf",
            final_url=_candidate().document_url,
        ),
    )
    session.commit()

    source = session.get(SourceDocument, result.source_document_id)
    assert source is not None
    assert source.source_organization == "Debt Management Office (DMO)"
    assert source.source_url == _candidate().document_url
    assert source.sha256 == result.sha256
    assert source.document_version == "domestic-2026-03-31"
    assert result.storage_path.endswith(f"domestic/2026-03-31/{result.sha256}.pdf")
    assert tmp_path.joinpath("domestic", "2026-03-31", f"{result.sha256}.pdf").read_bytes() == body


def test_archive_is_idempotent_by_sha256(session, tmp_path):
    body = b"%PDF-1.7\nsame bytes\n%%EOF"
    fetch = lambda _url: DmoDownload(  # noqa: E731 - compact deterministic test fixture
        body=body,
        content_type="application/pdf",
        final_url=_candidate().document_url,
    )

    first = archive_dmo_publication(session, _candidate(), archive_root=tmp_path, fetch=fetch)
    session.commit()
    second = archive_dmo_publication(session, _candidate(), archive_root=tmp_path, fetch=fetch)

    assert first.duplicate is False
    assert second.duplicate is True
    assert first.source_document_id == second.source_document_id
    assert len(session.scalars(select(SourceDocument)).all()) == 1


def test_archive_rejects_non_pdf_signature(session, tmp_path):
    with pytest.raises(ValueError, match="not a PDF"):
        archive_dmo_publication(
            session,
            _candidate(),
            archive_root=tmp_path,
            fetch=lambda _url: DmoDownload(
                body=b"<html>not pdf</html>",
                content_type="application/pdf",
                final_url=_candidate().document_url,
            ),
        )


def test_archive_rejects_off_host_redirect(session, tmp_path):
    with pytest.raises(ValueError, match="redirected outside"):
        archive_dmo_publication(
            session,
            _candidate(),
            archive_root=tmp_path,
            fetch=lambda _url: DmoDownload(
                body=b"%PDF-1.7\nfixture\n%%EOF",
                content_type="application/pdf",
                final_url="https://example.com/debt.pdf",
            ),
        )
