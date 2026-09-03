from __future__ import annotations

import argparse
import json
import uuid

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.dmo.approval import approve_debt_source, publish_debt_source
from gaiafaac_api.pipeline.dmo.archive import archive_dmo_publications
from gaiafaac_api.pipeline.dmo.discovery import discover_dmo_subnational_publications
from gaiafaac_api.pipeline.dmo.extract import extract_dmo_debt_source, extract_pending_debt_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC DMO source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "discover-subnational",
        help="Discover official DMO state/FCT debt publications without importing or publishing",
    )
    archive = commands.add_parser(
        "archive-subnational",
        help="Archive official DMO PDFs and register source metadata without extracting values",
    )
    archive.add_argument("--limit", type=int)
    extract = commands.add_parser(
        "extract-source",
        help="Extract one archived DMO source into unpublished review records",
    )
    extract.add_argument("source_document_id", type=uuid.UUID)
    commands.add_parser(
        "extract-pending",
        help="Extract every archived-but-unextracted DMO source (never publishes)",
    )
    approve = commands.add_parser(
        "approve-source",
        help="Human-verify a complete DMO debt source without publishing it",
    )
    approve.add_argument("source_document_id", type=uuid.UUID)
    approve.add_argument("reviewer_id", type=uuid.UUID)
    publish = commands.add_parser(
        "publish-source",
        help="Publish a human-verified DMO debt source into governed fiscal claims",
    )
    publish.add_argument("source_document_id", type=uuid.UUID)
    publish.add_argument("reviewer_id", type=uuid.UUID)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover-subnational":
        publications = discover_dmo_subnational_publications()
        print(
            json.dumps(
                [
                    {
                        "title": item.title,
                        "document_url": item.document_url,
                        "debt_kind": item.debt_kind,
                        "as_of_date": item.as_of_date.isoformat(),
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
    if args.command == "archive-subnational":
        with session_factory() as session:
            results = archive_dmo_publications(
                session,
                discover_dmo_subnational_publications(),
                limit=args.limit,
            )
            session.commit()
        print(
            json.dumps(
                [
                    {
                        "source_document_id": str(item.source_document_id),
                        "debt_kind": item.debt_kind,
                        "as_of_date": item.as_of_date,
                        "source_url": item.source_url,
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
            result = extract_dmo_debt_source(
                session,
                source_document_id=args.source_document_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "debt_kind": result.debt_kind,
                    "as_of_date": result.as_of_date,
                    "currency": result.currency,
                    "records_extracted": result.records_extracted,
                    "total_amount": format(result.total_amount, "f"),
                    "status": "extracted_awaiting_review",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "extract-pending":
        with session_factory() as session:
            outcomes = extract_pending_debt_sources(session)
        print(
            json.dumps(
                [
                    {
                        "source_document_id": outcome.source_document_id,
                        "status": outcome.status,
                        "records_extracted": outcome.records_extracted,
                        "total_amount": outcome.total_amount,
                        "error": outcome.error,
                    }
                    for outcome in outcomes
                ],
                indent=2,
                sort_keys=True,
            )
        )
        if any(outcome.status == "failed" for outcome in outcomes):
            raise SystemExit(2)
        return
    if args.command == "approve-source":
        with session_factory() as session:
            result = approve_debt_source(
                session,
                source_document_id=args.source_document_id,
                reviewer_id=args.reviewer_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "debt_kind": result.debt_kind,
                    "as_of_date": result.as_of_date,
                    "records_affected": result.records_affected,
                    "published": result.published,
                    "status": "human_verified_not_published",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "publish-source":
        with session_factory() as session:
            result = publish_debt_source(
                session,
                source_document_id=args.source_document_id,
                reviewer_id=args.reviewer_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "debt_kind": result.debt_kind,
                    "as_of_date": result.as_of_date,
                    "records_affected": result.records_affected,
                    "proof_count": len(result.proof_gaia_ids),
                    "published": result.published,
                    "status": "published_governed_claims",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
