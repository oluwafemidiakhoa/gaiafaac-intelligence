from gaiafaac_api.cli import build_parser


def test_collect_oagf_defaults():
    args = build_parser().parse_args(["collect-oagf"])
    assert args.command == "collect-oagf"
    assert args.months_back == 3
    assert args.dry_run is False


def test_collect_oagf_flags():
    args = build_parser().parse_args(["collect-oagf", "--months-back", "6", "--dry-run"])
    assert args.months_back == 6
    assert args.dry_run is True
