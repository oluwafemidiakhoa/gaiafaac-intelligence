from __future__ import annotations

import argparse
import uuid
from datetime import date
from pathlib import Path

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.national_distribution import (
    NationalDistributionImportRequest,
    approve_national_distribution,
    import_national_distribution,
    publish_national_distribution,
)
from gaiafaac_api.pipeline.national_scope import declare_national_states_scope


def _date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GaiaFAAC governed national FAAC reconciliation administration"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    collect = commands.add_parser(
        "collect",
        help=(
            "Discover, archive, validate and queue official national FAAC evidence "
            "(never publishes)"
        ),
    )
    collect.add_argument("--months-back", type=int, default=24)
    collect.add_argument("--max-pages", type=int, default=6)

    repair = commands.add_parser(
        "repair-autopilot",
        help=(
            "Re-extract unapproved unpublished national-autopilot packets with the "
            "hardened parser; quarantine unsafe official-source conflicts"
        ),
    )
    repair.add_argument(
        "--run-id",
        action="append",
        type=uuid.UUID,
        dest="run_ids",
        help="Limit repair to one extraction run; repeat for multiple runs.",
    )

    import_command = commands.add_parser(
        "import", help="Import official national distribution evidence into review"
    )
    import_command.add_argument("path", type=Path)
    import_command.add_argument("--reporting-period-id", type=uuid.UUID, required=True)
    import_command.add_argument("--source-organization", required=True)
    import_command.add_argument("--reported-unit", required=True)
    import_command.add_argument("--net-distributable-amount", required=True)
    import_command.add_argument("--federal-amount", required=True)
    import_command.add_argument("--states-amount", required=True)
    import_command.add_argument("--local-governments-amount", required=True)
    import_command.add_argument("--derivation-amount")
    import_command.add_argument(
        "--derivation-treatment",
        choices=["separate", "included_in_states", "not_reported"],
        default="separate",
    )
    import_command.add_argument("--gross-amount")
    import_command.add_argument("--deductions-amount")
    import_command.add_argument("--vat-amount")
    import_command.add_argument("--statutory-amount")
    import_command.add_argument("--publication-date", type=_date)
    import_command.add_argument("--source-url")
    import_command.add_argument("--document-version", default="1")
    import_command.add_argument(
        "--source-type",
        choices=[
            "canonical_national_evidence",
            "official_national_summary_evidence",
            "official_government_press_release",
        ],
        default="canonical_national_evidence",
    )
    import_command.add_argument(
        "--source-authority",
        choices=["canonical", "official_secondary", "contextual"],
        default="canonical",
    )
    import_command.add_argument(
        "--canonical-source-status",
        choices=["available", "missing", "superseded", "conflicted"],
        default="available",
    )

    scope = commands.add_parser(
        "declare-states-scope",
        help=(
            "Declare whether the official states aggregate includes the FCT when the "
            "source explicitly establishes that scope"
        ),
    )
    scope.add_argument("run_id", type=uuid.UUID)
    scope.add_argument(
        "--states-scope",
        required=True,
        choices=["states_only_36", "states_plus_fct_37"],
    )

    approve = commands.add_parser(
        "approve", help="Human-verify clean national distribution evidence"
    )
    approve.add_argument("run_id", type=uuid.UUID)
    approve.add_argument("--reviewer-id", type=uuid.UUID, required=True)
    approve.add_argument("--note")

    publish = commands.add_parser(
        "publish", help="Publish reviewed national evidence under four-eyes control"
    )
    publish.add_argument("run_id", type=uuid.UUID)
    publish.add_argument("--reviewer-id", type=uuid.UUID, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        if args.command == "collect":
            from gaiafaac_api.config import get_settings
            from gaiafaac_api.pipeline.national_evidence_hardened import (
                run_national_evidence_collection,
            )
            from gaiafaac_api.pipeline.national_notify import send_national_review_alert

            summary = run_national_evidence_collection(
                session,
                months_back=args.months_back,
                max_pages=args.max_pages,
            )
            settings = get_settings()
            queue_url = "https://gaiafaac-web.up.railway.app/review/national"
            for item in summary.queued:
                send_national_review_alert(
                    settings,
                    reporting_label=item.reporting_label,
                    run_id=item.run_id,
                    finding_count=item.finding_count,
                    blocking_finding_count=item.blocking_finding_count,
                    queue_url=queue_url,
                )
            print(
                "National collection complete: "
                f"checked={len(summary.checked_urls)}, "
                f"queued={len(summary.queued)}, "
                f"deferred={len(summary.deferred)}, "
                f"quarantined={len(summary.quarantined)}, "
                f"duplicates={len(summary.duplicates)}, "
                f"errors={len(summary.errors)}."
            )
        elif args.command == "repair-autopilot":
            from gaiafaac_api.pipeline.national_evidence_hardened import (
                repair_unpublished_national_evidence,
            )

            result = repair_unpublished_national_evidence(
                session,
                run_ids=set(args.run_ids) if args.run_ids else None,
            )
            print(
                "National autopilot repair complete: "
                f"repaired={len(result.repaired)}, "
                f"quarantined={len(result.quarantined)}, "
                f"duplicates={len(result.duplicates)}, "
                f"skipped={len(result.skipped)}."
            )
            for item in result.quarantined:
                print(f"QUARANTINED {item['run_id']} | {item['reason']}")
            for item in result.duplicates:
                print(
                    f"DUPLICATE {item['candidate_id']} | duplicate_of={item['duplicate_of']}"
                )
            for item in result.skipped:
                print(f"SKIPPED {item['run_id']} | {item['reason']}")
        elif args.command == "import":
            result = import_national_distribution(
                session,
                NationalDistributionImportRequest(
                    path=args.path,
                    reporting_period_id=args.reporting_period_id,
                    source_organization=args.source_organization,
                    reported_unit=args.reported_unit,
                    net_distributable_amount=args.net_distributable_amount,
                    federal_amount=args.federal_amount,
                    states_amount=args.states_amount,
                    local_governments_amount=args.local_governments_amount,
                    derivation_amount=args.derivation_amount,
                    derivation_treatment=args.derivation_treatment,
                    gross_amount=args.gross_amount,
                    deductions_amount=args.deductions_amount,
                    vat_amount=args.vat_amount,
                    statutory_amount=args.statutory_amount,
                    publication_date=args.publication_date,
                    source_url=args.source_url,
                    document_version=args.document_version,
                    source_type=args.source_type,
                    source_authority=args.source_authority,
                    canonical_source_status=args.canonical_source_status,
                ),
            )
            print(
                f"National evidence awaiting review: run={result.run_id}, "
                f"distribution={result.distribution_id}, findings={result.finding_count}, "
                f"blocking={result.blocking_finding_count}."
            )
        elif args.command == "declare-states-scope":
            declare_national_states_scope(
                session, run_id=args.run_id, states_scope=args.states_scope
            )
            print(f"National states scope declared: run={args.run_id}, scope={args.states_scope}.")
        elif args.command == "approve":
            result = approve_national_distribution(
                session,
                run_id=args.run_id,
                reviewer_id=args.reviewer_id,
                note=args.note,
            )
            print(
                f"National evidence approved: run={result.run_id}, "
                f"distribution={result.distribution_id}, published=false."
            )
        elif args.command == "publish":
            result = publish_national_distribution(
                session, run_id=args.run_id, reviewer_id=args.reviewer_id
            )
            print(
                f"National evidence PUBLISHED: run={result.run_id}, "
                f"distribution={result.distribution_id}, published=true."
            )


if __name__ == "__main__":
    main()
