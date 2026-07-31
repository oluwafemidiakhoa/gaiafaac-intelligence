from __future__ import annotations

import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)
MAX_DOWNLOAD_BYTES = 30 * 1024 * 1024
Fetch = Callable[[str], bytes | None]


def _urlopen_bytes(url: str) -> bytes | None:
    request = urllib.request.Request(  # noqa: S310 - fixed https OAGF host
        url, headers={"User-Agent": "GaiaFAAC-collector/1.0 (research)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
            return response.read(MAX_DOWNLOAD_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def http_download(
    url: str, *, dest_dir: Path = Path("data/raw"), fetch: Fetch = _urlopen_bytes
) -> Path | None:
    """Download a URL to dest_dir if it is a real (non-empty, in-limit) PDF."""
    data = fetch(url)
    if data is None:
        logger.info("Not published yet (404): %s", url)
        return None
    if not data.startswith(b"%PDF"):
        logger.warning("Ignoring non-PDF response from %s", url)
        return None
    if len(data) > MAX_DOWNLOAD_BYTES:
        logger.warning("Ignoring oversized response from %s", url)
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / url.rsplit("/", 1)[-1]
    destination.write_bytes(data)
    return destination
