from __future__ import annotations

import argparse
import json

from gaiafaac_api.pipeline.dmo.discovery import discover_dmo_subnational_publications


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC DMO source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "discover-subnational",
        help="Discover official DMO state/FCT debt publications without importing or publishing",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover-subnational":
        publications = discover_dmo_subnational_publications()
        print(
            json.dumps(
                [
                    {
                        "title": item.title,
                        "document_url": item.document_url,
                        "debt_kind": item.debt_kind,
                        "as_of_date": item.as_of_date.isoformat(),
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
