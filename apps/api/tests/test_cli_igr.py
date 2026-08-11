import uuid
from pathlib import Path

from gaiafaac_api.cli import build_parser


def test_import_nbs_igr_cli_arguments():
    args = build_parser().parse_args(
        [
            "import-nbs-igr",
            "/app/data/raw/IGR_2024.zip",
            "--year",
            "2024",
        ]
    )

    assert args.command == "import-nbs-igr"
    assert args.path == Path("/app/data/raw/IGR_2024.zip")
    assert args.year == 2024
    assert args.source_url is None


def test_approve_igr_cli_arguments():
    source_id = uuid.uuid4()
    reviewer_id = uuid.uuid4()
    args = build_parser().parse_args(
        [
            "approve-igr",
            str(source_id),
            "--reviewer-id",
            str(reviewer_id),
        ]
    )

    assert args.command == "approve-igr"
    assert args.source_document_id == source_id
    assert args.reviewer_id == reviewer_id


def test_publish_igr_cli_arguments():
    source_id = uuid.uuid4()
    reviewer_id = uuid.uuid4()
    args = build_parser().parse_args(
        [
            "publish-igr",
            str(source_id),
            "--reviewer-id",
            str(reviewer_id),
        ]
    )

    assert args.command == "publish-igr"
    assert args.source_document_id == source_id
    assert args.reviewer_id == reviewer_id
