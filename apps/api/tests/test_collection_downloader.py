from pathlib import Path

from gaiafaac_api.pipeline.collection.downloader import http_download

URL = "https://oagf.gov.ng/wp-content/uploads/2024/02/Disbursement-January-2024.pdf"


def test_saves_pdf_bytes(tmp_path: Path):
    path = http_download(URL, dest_dir=tmp_path, fetch=lambda _u: b"%PDF-1.7 fake body")
    assert path is not None
    assert path.exists()
    assert path.read_bytes().startswith(b"%PDF")
    assert path.name == "Disbursement-January-2024.pdf"


def test_returns_none_on_404(tmp_path: Path):
    assert http_download(URL, dest_dir=tmp_path, fetch=lambda _u: None) is None


def test_rejects_non_pdf(tmp_path: Path):
    assert http_download(URL, dest_dir=tmp_path, fetch=lambda _u: b"<html>nope</html>") is None
