from __future__ import annotations

import calendar

_BASE = "https://oagf.gov.ng/wp-content/uploads"


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def candidate_urls(revenue_year: int, revenue_month: int) -> list[str]:
    """OAGF PDF URLs for a revenue month, most-likely publication folder first.

    The filename carries the revenue month name + revenue year; the upload folder
    is the publication month (revenue month + 1, with +2 as a slippage fallback).
    """
    month_name = calendar.month_name[revenue_month]
    filename = f"Disbursement-{month_name}-{revenue_year}.pdf"
    urls: list[str] = []
    for slip in (1, 2):
        pub_year, pub_month = _add_months(revenue_year, revenue_month, slip)
        urls.append(f"{_BASE}/{pub_year}/{pub_month:02d}/{filename}")
    return urls
