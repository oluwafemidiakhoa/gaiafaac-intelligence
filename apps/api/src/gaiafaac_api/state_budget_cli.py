from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.state_budget.approval import (
    approve_budget_source,
    publish_budget_source,
)
from gaiafaac_api.pipeline.state_budget.archive import archive_state_budget_publications
from gaiafaac_api.pipeline.state_budget.discovery import (
    discover_state_budget_publications,
    registered_budget_portals,
)
from gaiafaac_api.pipeline.state_budget.extract import extract_state_budget_source
from gaiafaac_api.pipeline.state_budget.performance_archive import (
    archive_budget_performance_publications,
)
from gaiafaac_api.pipeline.state_budget.performance_discovery import (
    discover_budget_performance_publications,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC state-budget source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "list-portals",
        help="List verified official state-budget portals currently registered",
    )
    discover = commands.add_parser(
        "discover-state",
        help="Discover approved-budget publications for one registered state without importing",
    )
    discover.add_argument("state_code")
    discover_performance = commands.add_parser(
        "discover-performance",
        help="Discover quarterly budget-performance reports without importing values",
    )
    discover_performance.add_argument("state_code")
    archive = commands.add_parser(
        "archive-state",
        help="Archive approved-budget artifacts for one registered state without extracting values",
    )
    archive.add_argument("state_code")
    archive.add_argument("--archive-root", type=Path, default=Path("data/raw/state-budget"))
    archive.add_argument("--limit", type=int)
    archive_performance = commands.add_parser(
        "archive-performance",
        help="Archive quarterly budget-performance artifacts without extracting values",
    )
    archive_performance.add_argument("state_code")
    archive_performance.add_argument(
        "--archive-root",
        type=Path,
        default=Path("data/raw/state-budget-performance"),
    )
    archive_performance.add_argument("--limit", type=int)
    extract = commands.add_parser(
        "extract-source",
        help="Extract one archived supported state budget into unpublished review records",
    )
    extract.add_argument("source_document_id", type=uuid.UUID)
    approve = commands.add_parser(
        "approve-source",
        help="Human-verify one complete staged state budget without publishing claims",
    )
    approve.add_argument("source_document_id", type=uuid.UUID)
    approve.add_argument("reviewer_id", type=uuid.UUID)
    publish = commands.add_parser(
        "publish-source",
        help="Publish one approved state budget into governed budget claims",
    )
    publish.add_argument("source_document_id", type=uuid.UUID)
    publish.add_argument("reviewer_id", type=uuid.UUID)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list-portals":
        portals = registered_budget_portals()
        print(
            json.dumps(
                {
                    "registered_count": len(portals),
                    "expected_jurisdictions": 37,
                    "coverage_complete": len(portals) == 37,
                    "portals": [
                        {
                            "state_code": portal.state_code,
                            "state_name": portal.state_name,
                            "listing_url": portal.listing_url,
                            "status": "verified_registry_entry",
                        }
                        for portal in portals
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "discover-state":
        publications = discover_state_budget_publications(args.state_code)
        print(
            json.dumps(
                [
                    {
                        "state_code": item.state_code,
                        "state_name": item.state_name,
                        "fiscal_year": item.fiscal_year,
                        "title": item.title,
                        "document_url": item.document_url,
                        "listing_url": item.listing_url,
                        "status": "discovered_only",
                    }
                    for item in publications
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "discover-performance":
        publications = discover_budget_performance_publications(args.state_code)
        print(
            json.dumps(
                [
                    {
                        "state_code": item.state_code,
                        "state_name": item.state_name,
                        "fiscal_year": item.fiscal_year,
                        "quarter": item.quarter,
                        "title": item.title,
                        "document_url": item.document_url,
                        "listing_url": item.listing_url,
                        "status": "discovered_performance_only",
                    }
                    for item in publications
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "archive-state":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            results = archive_state_budget_publications(
                session,
                discover_state_budget_publications(args.state_code),
                archive_root=args.archive_root,
                limit=args.limit,
            )
            session.commit()
        print(
            json.dumps(
                [
                    {
                        "source_document_id": str(item.source_document_id),
                        "state_code": item.state_code,
                        "fiscal_year": item.fiscal_year,
                        "document_url": item.document_url,
                        "artifact_url": item.artifact_url,
                        "artifact_kind": item.artifact_kind,
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
    if args.command == "archive-performance":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            results = archive_budget_performance_publications(
                session,
                discover_budget_performance_publications(args.state_code),
                archive_root=args.archive_root,
                limit=args.limit,
            )
            session.commit()
        print(
            json.dumps(
                [
                    {
                        "source_document_id": str(item.source_document_id),
                        "state_code": item.state_code,
                        "fiscal_year": item.fiscal_year,
                        "quarter": item.quarter,
                        "document_url": item.document_url,
                        "artifact_url": item.artifact_url,
                        "artifact_kind": item.artifact_kind,
                        "sha256": item.sha256,
                        "storage_path": item.storage_path,
                        "duplicate": item.duplicate,
                        "status": "archived_performance_registered_only",
                    }
                    for item in results
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "extract-source":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            result = extract_state_budget_source(
                session,
                source_document_id=args.source_document_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "state_code": result.state_code,
                    "fiscal_year": result.fiscal_year,
                    "records_extracted": result.records_extracted,
                    "total_expenditure": str(result.total_expenditure),
                    "status": "requires_review",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "approve-source":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            result = approve_budget_source(
                session,
                source_document_id=args.source_document_id,
                reviewer_id=args.reviewer_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "state_code": result.state_code,
                    "fiscal_year": result.fiscal_year,
                    "records_affected": result.records_affected,
                    "published": result.published,
                    "status": "approved_not_published",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "publish-source":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            result = publish_budget_source(
                session,
                source_document_id=args.source_document_id,
                reviewer_id=args.reviewer_id,
            )
        print(
            json.dumps(
                {
                    "source_document_id": result.source_document_id,
                    "state_code": result.state_code,
                    "fiscal_year": result.fiscal_year,
                    "records_affected": result.records_affected,
                    "published": result.published,
                    "proof_gaia_ids": list(result.proof_gaia_ids),
                    "status": "published_governed_budget_claims",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
