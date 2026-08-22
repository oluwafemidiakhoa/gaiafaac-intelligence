from __future__ import annotations

import argparse
import json

from gaiafaac_api.pipeline.state_financials.discovery import (
    discover_state_financial_publications,
    registered_state_financial_portals,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gaia Fiscal state financial-evidence source administration"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "list-portals",
        help="List verified official state financial-evidence portals currently registered",
    )
    discover = commands.add_parser(
        "discover-state",
        help="Discover audited statements and explicit liability registers without importing",
    )
    discover.add_argument("state_code")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list-portals":
        portals = registered_state_financial_portals()
        print(
            json.dumps(
                {
                    "registered_portals": len(portals),
                    "registered_jurisdictions": len({portal.state_code for portal in portals}),
                    "expected_jurisdictions": 37,
                    "coverage_complete": len({portal.state_code for portal in portals}) == 37,
                    "portals": [
                        {
                            "state_code": portal.state_code,
                            "state_name": portal.state_name,
                            "listing_url": portal.listing_url,
                            "evidence_kinds": sorted(kind.value for kind in portal.evidence_kinds),
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
        publications = discover_state_financial_publications(args.state_code)
        print(
            json.dumps(
                [
                    {
                        "state_code": item.state_code,
                        "state_name": item.state_name,
                        "fiscal_year": item.fiscal_year,
                        "evidence_kind": item.evidence_kind.value,
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
