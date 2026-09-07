"""Generate read-only pre-release previews, without orders or payment calls."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

from gaiafaac_api.services.institutional_one_time_exports import (
    build_one_time_excel,
    build_one_time_pdf,
)


def main() -> None:
    out = Path("qa-out")
    out.mkdir(exist_ok=True)
    url = (
        "https://gaiafaac-api-production.up.railway.app"
        "/api/v1/published/decision-packet/lagos?year=2026"
    )
    with urlopen(url, timeout=30) as response:
        packet = json.load(response)
    if not packet.get("months"):
        raise RuntimeError("Published evidence unavailable; no sample was inferred.")
    artifact = {
        "schema": "gaia-sample-decision-pack-v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "request": {"state_slug": "lagos", "year": 2026, "sample": True},
        "decision_packet": packet,
        "statement": "PRE-RELEASE QA SAMPLE / NOT FOR RELIANCE / NOT FOR RESALE",
    }
    (out / "pre-release-sample-artifact.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )
    for extension, build in (("xlsx", build_one_time_excel), ("pdf", build_one_time_pdf)):
        _, _, body = build(
            purchase_id="SAMPLE-lagos-2026",
            product_code="decision_pack",
            amount_naira="50000",
            currency="NGN",
            completed_at="Not applicable - demonstration sample",
            artifact=artifact,
            sample=True,
            jurisdiction="Lagos",
        )
        (out / f"pre-release-lagos-2026-sample.{extension}").write_bytes(body)
    (out / "qa-context.json").write_text(
        json.dumps(
            {
                "commit": os.environ.get("GITHUB_SHA"),
                "source": url,
                "scope": "Public evidence rendered by this PR; not production issuance",
                "captured_at": artifact["captured_at"],
                "published_periods": len(packet["months"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Generated native XLSX/PDF previews from one public-evidence capture.")


if __name__ == "__main__":
    main()
