from __future__ import annotations

import argparse
from datetime import UTC, datetime

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.services.alert_delivery import deliver_customer_alerts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deliver opted-in GaiaFAAC customer alert emails."
    )
    parser.add_argument("--year", type=int, default=datetime.now(UTC).year)
    parser.add_argument("--max-attempts", type=int, default=5)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not 2000 <= args.year <= 2100:
        raise SystemExit("--year must be between 2000 and 2100")
    if not 1 <= args.max_attempts <= 20:
        raise SystemExit("--max-attempts must be between 1 and 20")

    settings = get_settings()
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        summary = deliver_customer_alerts(
            session,
            settings,
            year=args.year,
            max_attempts=args.max_attempts,
        )
    print(
        "Customer alert delivery complete: "
        f"users={summary.users_checked}, eligible={summary.alerts_eligible}, "
        f"sent={summary.sent}, failed={summary.failed}, deferred={summary.deferred}, "
        f"already_sent={summary.skipped_sent}."
    )


if __name__ == "__main__":
    main()
