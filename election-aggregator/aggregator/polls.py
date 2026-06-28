"""Scrape aggregated opinion polls from Wikipedia.

Wikipedia maintains a maintained, uniformly-structured table per election:
"Opinion polling for the YEAR Israeli legislative election". Each row is one
published poll — fieldwork date, pollster, sample size and projected seats per
party. That makes it the most practical machine-readable poll aggregator for
Israel (there is no official poll API).

We pull the rendered HTML via the MediaWiki API and parse tables with pandas.
The page layout changes occasionally (merged header cells, footnote markers), so
:func:`extract_polls` is best-effort: it returns the largest plausible poll
table with lightly cleaned headers. Inspect the result before trusting column
alignment for a new election.

Needs outbound access to ``en.wikipedia.org``.
"""

from __future__ import annotations

import io
import re

import pandas as pd
import requests

from .config import WIKIPEDIA_API, WIKIPEDIA_POLL_PAGES

_TIMEOUT = 60
_HEADERS = {"User-Agent": "israel-election-aggregator/0.1 (research; contact via repo)"}


def fetch_poll_html(year: int) -> str:
    """Return the rendered HTML of the poll page for ``year``."""
    try:
        title = WIKIPEDIA_POLL_PAGES[year]
    except KeyError as exc:
        raise KeyError(
            f"no Wikipedia poll page configured for {year}; "
            f"add it to WIKIPEDIA_POLL_PAGES"
        ) from exc
    resp = requests.get(
        WIKIPEDIA_API,
        params={
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        },
        headers=_HEADERS,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "error" in payload:
        raise RuntimeError(f"Wikipedia API error: {payload['error']}")
    return payload["parse"]["text"]


def _clean_header(name) -> str:
    """Flatten a (possibly multi-index) header cell to a clean string."""
    if isinstance(name, tuple):
        parts = [str(p) for p in name if p and not str(p).startswith("Unnamed")]
        name = parts[-1] if parts else ""
    name = re.sub(r"\[.*?\]", "", str(name))  # drop footnote markers
    return name.strip()


def parse_poll_tables(html: str) -> list[pd.DataFrame]:
    """Parse every HTML table on the page into DataFrames."""
    return pd.read_html(io.StringIO(html))


def _looks_like_poll_table(df: pd.DataFrame) -> bool:
    headers = " ".join(_clean_header(c).lower() for c in df.columns)
    has_pollster = any(k in headers for k in ("pollster", "polling", "source"))
    has_date = "date" in headers or "fieldwork" in headers
    return (has_pollster or has_date) and df.shape[1] >= 6 and len(df) >= 3


def extract_polls(year: int, html: str | None = None) -> pd.DataFrame:
    """Return a best-effort tidy table of polls for ``year``.

    Picks the largest table that looks like a poll table and cleans its headers.
    Raises ``LookupError`` if no plausible poll table is found.
    """
    if html is None:
        html = fetch_poll_html(year)
    tables = parse_poll_tables(html)
    candidates = [t for t in tables if _looks_like_poll_table(t)]
    if not candidates:
        raise LookupError(f"no poll-shaped table found on the {year} page")
    best = max(candidates, key=lambda t: t.shape[0] * t.shape[1])
    best = best.copy()
    best.columns = [_clean_header(c) for c in best.columns]
    # Strip footnote markers (e.g. "Panels[1]") from string cells.
    for col in best.columns:
        if pd.api.types.is_string_dtype(best[col]) or best[col].dtype == object:
            best[col] = best[col].map(
                lambda v: re.sub(r"\[.*?\]", "", v).strip() if isinstance(v, str) else v
            )
    return best
