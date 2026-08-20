from __future__ import annotations

import argparse
import json

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.services.institutional_webhooks import run_webhook_delivery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deliver Gaia institutional fiscal webhooks")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--max-deliveries", type=int, default=500)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.max_attempts < 1:
        raise SystemExit("--max-attempts must be at least 1")
    if args.max_deliveries < 1:
        raise SystemExit("--max-deliveries must be at least 1")
    settings = get_settings()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        summary = run_webhook_delivery(
            session,
            settings,
            max_attempts=args.max_attempts,
            max_deliveries=args.max_deliveries,
        )
    print(json.dumps(summary.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
