from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.dmo.archive import archive_dmo_publications
from gaiafaac_api.pipeline.dmo.discovery import discover_dmo_subnational_publications


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
    archive.add_argument("--archive-root", type=Path, default=Path("data/raw/dmo"))
    archive.add_argument("--limit", type=int)
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
    if args.command == "archive-subnational":
        session_factory = create_session_factory(create_database_engine())
        with session_factory() as session:
            results = archive_dmo_publications(
                session,
                discover_dmo_subnational_publications(),
                archive_root=args.archive_root,
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
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
