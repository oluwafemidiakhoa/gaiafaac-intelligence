from __future__ import annotations

import argparse
import uuid
from datetime import date
from pathlib import Path

from gaiafaac_api.database.models import ExtractionRun
from gaiafaac_api.database.seeds import seed_demo_allocations, seed_states
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics
from gaiafaac_api.pipeline.approval import approve_import, reject_import
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest, import_allocations_csv
from gaiafaac_api.pipeline.validation import validate_import
from gaiafaac_api.services.source_documents import register_source_document


def _date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC database administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed-states", help="Seed the 36 states and FCT")

    source = commands.add_parser("register-source", help="Register source-document metadata")
    source.add_argument("path", type=Path)
    source.add_argument("--source-organization", required=True)
    source.add_argument("--publication-date", type=_date)
    source.add_argument("--mime-type")
    source.add_argument("--source-url")
    source.add_argument("--document-version", default="1")

    demo = commands.add_parser("seed-demo", help="Load clearly labelled synthetic demo data")
    demo.add_argument(
        "--csv",
        type=Path,
        default=Path("database/seeds/demo_state_allocations.csv"),
    )

    import_command = commands.add_parser(
        "import-allocations", help="Run the controlled CSV allocation import"
    )
    import_command.add_argument("path", type=Path)
    import_command.add_argument("--source-organization", required=True)
    import_command.add_argument("--revenue-month", required=True, type=_date)
    import_command.add_argument("--reporting-label", required=True)
    import_command.add_argument("--faac-meeting-date", type=_date)
    import_command.add_argument("--publication-date", type=_date)
    import_command.add_argument("--source-url")
    import_command.add_argument("--document-version", default="1")
    import_command.add_argument("--demo", action="store_true")

    validate = commands.add_parser(
        "validate-import", help="Re-run validation for an extraction run"
    )
    validate.add_argument("run_id", type=uuid.UUID)

    approve = commands.add_parser("approve-import", help="Explicitly human-verify a clean import")
    approve.add_argument("run_id", type=uuid.UUID)
    approve.add_argument("--reviewer-id", required=True, type=uuid.UUID)

    reject = commands.add_parser("reject-import", help="Explicitly reject an import")
    reject.add_argument("run_id", type=uuid.UUID)
    reject.add_argument("--reviewer-id", required=True, type=uuid.UUID)
    reject.add_argument("--reason", required=True)

    commands.add_parser("seed-analytics-demo", help="Generate the synthetic analytics demo dataset")
    commands.add_parser("compute-analytics", help="Compute and persist demo analytics")

    file_import = commands.add_parser(
        "import-file", help="Import a real source file (CSV/XLSX/OAGF PDF) through review"
    )
    file_import.add_argument("path", type=Path)
    file_import.add_argument("--source-organization", required=True)
    file_import.add_argument("--revenue-month", required=True, type=_date)
    file_import.add_argument("--reporting-label", required=True)
    file_import.add_argument("--faac-meeting-date", type=_date)
    file_import.add_argument("--publication-date", type=_date)
    file_import.add_argument("--source-url")
    file_import.add_argument("--document-version", default="1")
    file_import.add_argument(
        "--reported-unit", help="Explicit unit for rows without one, e.g. naira"
    )
    file_import.add_argument("--demo", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        if args.command == "seed-states":
            changed = seed_states(session)
            print(f"State seed complete: {changed} rows inserted or updated.")
        elif args.command == "register-source":
            document = register_source_document(
                session,
                path=args.path,
                source_organization=args.source_organization,
                publication_date=args.publication_date,
                mime_type=args.mime_type,
                source_url=args.source_url,
                document_version=args.document_version,
            )
            print(f"Source registered: {document.id} ({document.sha256})")
        elif args.command == "seed-demo":
            inserted = seed_demo_allocations(session, args.csv)
            print(f"DEMO DATA seed complete: {inserted} synthetic allocations inserted.")
        elif args.command == "import-allocations":
            result = import_allocations_csv(
                session,
                ImportRequest(
                    path=args.path,
                    source_organization=args.source_organization,
                    revenue_month=args.revenue_month,
                    reporting_label=args.reporting_label,
                    faac_meeting_date=args.faac_meeting_date,
                    publication_date=args.publication_date,
                    source_url=args.source_url,
                    document_version=args.document_version,
                    is_demo=args.demo,
                ),
            )
            print(
                f"Import awaiting review: run={result.run_id}, "
                f"records={result.records_extracted}, "
                f"findings={result.finding_count}, "
                f"blocking={result.blocking_finding_count}."
            )
        elif args.command == "validate-import":
            run = session.get(ExtractionRun, args.run_id)
            if run is None:
                raise SystemExit(f"Extraction run does not exist: {args.run_id}")
            results = validate_import(session, run)
            session.commit()
            print(f"Validation complete: run={run.id}, findings={len(results)}.")
        elif args.command == "approve-import":
            result = approve_import(session, run_id=args.run_id, reviewer_id=args.reviewer_id)
            print(
                f"Import approved: run={result.run_id}, "
                f"allocations={result.allocations_approved}, published=false."
            )
        elif args.command == "reject-import":
            result = reject_import(
                session,
                run_id=args.run_id,
                reviewer_id=args.reviewer_id,
                reason=args.reason,
            )
            print(f"Import rejected: run={result.run_id}, published=false.")
        elif args.command == "seed-analytics-demo":
            summary = generate_analytics_dataset(session)
            print(
                f"Analytics dataset ready: periods={summary.periods}, "
                f"allocations={summary.allocations}, components={summary.components}."
            )
        elif args.command == "compute-analytics":
            result = compute_analytics(session)
            print(
                f"Analytics computed: indicators={result.indicators}, forecasts={result.forecasts}."
            )
        elif args.command == "import-file":
            result = import_file(
                session,
                ImportRequest(
                    path=args.path,
                    source_organization=args.source_organization,
                    revenue_month=args.revenue_month,
                    reporting_label=args.reporting_label,
                    faac_meeting_date=args.faac_meeting_date,
                    publication_date=args.publication_date,
                    source_url=args.source_url,
                    document_version=args.document_version,
                    reported_unit=args.reported_unit,
                    is_demo=args.demo,
                ),
            )
            print(
                f"File import awaiting review: run={result.run_id}, "
                f"records={result.records_extracted}, "
                f"findings={result.finding_count}, "
                f"blocking={result.blocking_finding_count}."
            )


if __name__ == "__main__":
    main()
