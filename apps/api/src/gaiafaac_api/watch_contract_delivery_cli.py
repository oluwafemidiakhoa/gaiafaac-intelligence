from __future__ import annotations

import argparse
import json

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.services.watch_contract_delivery import run_watch_delivery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deliver Gaia Watch Contract operational reviews by configured outbound channels"
    )
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--max-deliveries", type=int, default=500)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not 1 <= args.max_attempts <= 20:
        raise SystemExit("--max-attempts must be between 1 and 20")
    if not 1 <= args.max_deliveries <= 5000:
        raise SystemExit("--max-deliveries must be between 1 and 5000")

    settings = get_settings()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        summary = run_watch_delivery(
            session,
            settings,
            max_attempts=args.max_attempts,
            max_deliveries=args.max_deliveries,
        )
    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
