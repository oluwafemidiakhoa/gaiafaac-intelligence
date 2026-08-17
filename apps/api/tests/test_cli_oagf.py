from datetime import date

from gaiafaac_api.cli import build_parser


def test_sync_oagf_defaults_to_all_categories_without_extraction() -> None:
    args = build_parser().parse_args(["sync-oagf-publications"])

    assert args.dry_run is False
    assert args.category is None
    assert args.since is None
    assert args.download_only is False
    assert args.extract is False
    assert args.limit is None


def test_sync_oagf_accepts_controlled_flags() -> None:
    args = build_parser().parse_args(
        [
            "sync-oagf-publications",
            "--dry-run",
            "--category",
            "faac-report",
            "--since",
            "2026-01-01",
            "--download-only",
            "--limit",
            "12",
        ]
    )

    assert args.dry_run is True
    assert args.category == "faac-report"
    assert args.since == date(2026, 1, 1)
    assert args.download_only is True
    assert args.limit == 12
