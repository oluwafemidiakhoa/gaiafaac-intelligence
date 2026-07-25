from gaiafaac_api.cli import build_parser


def test_parser_accepts_analytics_commands() -> None:
    parser = build_parser()
    assert parser.parse_args(["seed-analytics-demo"]).command == "seed-analytics-demo"
    assert parser.parse_args(["compute-analytics"]).command == "compute-analytics"
