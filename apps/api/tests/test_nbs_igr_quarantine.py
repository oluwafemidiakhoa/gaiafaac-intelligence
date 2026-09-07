from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.igr_models import StateIgrRecord
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.nbs_igr.extract import extract_pending_igr_sources


def test_contract_failure_is_quarantined_without_staging_partial_rows(session, tmp_path):
    seed_states(session)
    path = tmp_path / "legacy-2016.pdf"
    path.write_bytes(b"%PDF-test")
    source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/551",
        original_filename="legacy-2016.pdf",
        storage_path=str(path),
        sha256="9" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version="igr-2016-report-551",
        is_demo=False,
    )
    session.add(source)
    session.commit()

    outcomes = extract_pending_igr_sources(
        session,
        text_reader=lambda _path: [(1, "legacy layout with no supported deterministic rows")],
    )

    assert len(outcomes) == 1
    assert outcomes[0].source_document_id == str(source.id)
    assert outcomes[0].status == "failed"
    assert outcomes[0].error is not None
    assert "jurisdiction coverage failed" in outcomes[0].error

    refreshed = session.get(SourceDocument, source.id)
    assert refreshed is not None
    assert refreshed.processing_status is ProcessingStatus.FAILED
    assert refreshed.source_status is SourceStatus.REGISTERED
    assert (
        session.scalar(
            select(StateIgrRecord.id).where(StateIgrRecord.source_document_id == source.id)
        )
        is None
    )

    # FAILED sources are intentionally excluded from future scheduled pending extraction.
    assert extract_pending_igr_sources(session, text_reader=lambda _path: []) == []
