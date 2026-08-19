from __future__ import annotations

import argparse
import uuid

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.lga_ledger import (
    approve_lga_review,
    import_lga_table_iv_from_archive,
    publish_lga_review,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GaiaFAAC governed OAGF Table IV local-government administration"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    import_command = commands.add_parser(
        "import",
        help="Extract retained OAGF Table IV into an unpublished 774-jurisdiction review batch",
    )
    import_command.add_argument("--source-document-id", type=uuid.UUID, required=True)

    approve = commands.add_parser(
        "approve",
        help="Human-verify a complete clean LGA review batch",
    )
    approve.add_argument("review_id", type=uuid.UUID)
    approve.add_argument("--reviewer-id", type=uuid.UUID, required=True)

    publish = commands.add_parser(
        "publish",
        help="Publish approved LGA evidence under four-eyes control",
    )
    publish.add_argument("review_id", type=uuid.UUID)
    publish.add_argument("--publisher-id", type=uuid.UUID, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        if args.command == "import":
            review = import_lga_table_iv_from_archive(
                session,
                source_document_id=args.source_document_id,
            )
            print(
                "LGA Table IV awaiting review: "
                f"review={review.id}, records={review.record_count}, "
                f"blocking={review.blocking_count}, status={review.status}."
            )
        elif args.command == "approve":
            review = approve_lga_review(
                session,
                review_id=args.review_id,
                reviewer_id=args.reviewer_id,
            )
            print(
                f"LGA evidence approved: review={review.id}, "
                f"records={review.record_count}, published=false."
            )
        elif args.command == "publish":
            review = publish_lga_review(
                session,
                review_id=args.review_id,
                publisher_id=args.publisher_id,
            )
            print(
                f"LGA evidence PUBLISHED: review={review.id}, "
                f"records={review.record_count}, published=true."
            )


if __name__ == "__main__":
    main()
