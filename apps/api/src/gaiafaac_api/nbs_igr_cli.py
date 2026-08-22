from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.nbs_igr.archive import archive_nbs_igr_publications
from gaiafaac_api.pipeline.nbs_igr.discovery import discover_nbs_igr_publications
from gaiafaac_api.pipeline.nbs_igr.extract import extract_nbs_igr_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC NBS IGR source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "discover-reports",
        help="Discover official NBS state-level IGR reports without importing or publishing",
    )
    archive = commands.add_parser(
        "archive-reports",
        help="Archive official NBS IGR PDFs and register metadata without extracting values",
    )
    archive.add_argument("--archive-root", type=Path, default=Path("data/raw/nbs/igr"))
    archive.add_argument("--limit", type=int)
    extract = commands.add_parser(
        "extract-source",
        help="Extract one archived NBS IGR report into unpublished review records",
    )
    extract.add_argument("source_document_id", type=uuid.UUID)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover-reports":
        publications = discover_nbs_igr_publications()
        print(
            json.dumps(
                [
                    {
                        "title": item.title,
                        "report_url": item.report_url,
                        "report_id": item.report_id,
                        "fiscal_year": item.fiscal_year,
                        "status": "discovered_only",
                    }
                    for item in publications
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    session_factory = create_session_factory(create_database_engine())
    if args.command == "archive-reports":
        with session_factory() as session:
            results = archive_nbs_igr_publications(
                session,
                discover_nbs_igr_publications(),
                archive_root=args.archive_root,
                limit=args.limit,
            )
            session.commit()
        print(
            json.dumps(
                [
                    {
                        "source_document_id": str(item.source_document_id),
                        "report_id": item.report_id,
                        "fiscal_year": item.fiscal_year,
                        "report_url": item.report_url,
                        "artifact_url": item.artifact_url,
                        "sha256": item.sha256,
                        "storage_path": item.storage_path,
                        "duplicate": item.duplicate,
                        "status": "archived_registered_only",
                    }
                    for item in results
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "extract-source":
        with session_factory() as session:
            result = extract_nbs_igr_source(
                session,
                source_document_id=args.source_document_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "fiscal_year": result.fiscal_year,
                    "records_extracted": result.records_extracted,
                    "total_amount": format(result.total_amount, "f"),
                    "status": "extracted_awaiting_review",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
