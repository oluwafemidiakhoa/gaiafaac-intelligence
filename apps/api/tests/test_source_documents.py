import hashlib
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.services.source_documents import register_source_document


def test_source_registration_records_checksum_and_is_idempotent(
    session: Session, tmp_path: Path
) -> None:
    path = tmp_path / "statement.pdf"
    content = b"test-only source document"
    path.write_bytes(content)

    first = register_source_document(
        session,
        path=path,
        source_organization="Test publisher",
        publication_date=date(2026, 7, 1),
    )
    second = register_source_document(
        session,
        path=path,
        source_organization="Test publisher",
        publication_date=date(2026, 7, 1),
    )

    assert first.id == second.id
    assert first.sha256 == hashlib.sha256(content).hexdigest()
    assert first.storage_path == str(path.resolve())
    assert first.processing_status is ProcessingStatus.REGISTERED
    assert first.source_status is SourceStatus.REGISTERED
    assert session.scalar(select(func.count()).select_from(SourceDocument)) == 1
