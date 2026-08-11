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
