from __future__ import annotations

import argparse
import json

from gaiafaac_api.pipeline.state_budget.discovery import (
    discover_state_budget_publications,
    registered_budget_portals,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC state-budget source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "list-portals",
        help="List verified official state-budget portals currently registered",
    )
    discover = commands.add_parser(
        "discover-state",
        help="Discover approved-budget publications for one registered state without importing",
    )
    discover.add_argument("state_code")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list-portals":
        portals = registered_budget_portals()
        print(
            json.dumps(
                {
                    "registered_count": len(portals),
                    "expected_jurisdictions": 37,
                    "coverage_complete": len(portals) == 37,
                    "portals": [
                        {
                            "state_code": portal.state_code,
                            "state_name": portal.state_name,
                            "listing_url": portal.listing_url,
                            "status": "verified_registry_entry",
                        }
                        for portal in portals
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "discover-state":
        publications = discover_state_budget_publications(args.state_code)
        print(
            json.dumps(
                [
                    {
                        "state_code": item.state_code,
                        "state_name": item.state_name,
                        "fiscal_year": item.fiscal_year,
                        "title": item.title,
                        "document_url": item.document_url,
                        "listing_url": item.listing_url,
                        "status": "discovered_only",
                    }
                    for item in publications
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
