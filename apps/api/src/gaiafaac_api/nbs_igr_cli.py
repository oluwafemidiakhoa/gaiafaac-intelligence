from __future__ import annotations

import argparse
import json

from gaiafaac_api.pipeline.nbs_igr.discovery import discover_nbs_igr_publications


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GaiaFAAC NBS IGR source administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "discover-reports",
        help="Discover official NBS state-level IGR reports without importing or publishing",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "discover-reports":
        publications = discover_nbs_igr_publications()
        print(
            json.dumps(
                [
                    {
                        "title": item.title,
                        "report_url": item.report_url,
                        "report_id": item.report_id,
                        "fiscal_year": item.fiscal_year,
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
