"""Fetch official per-kalpi Knesset results from data.gov.il (CKAN).

The ``votes-knesset`` dataset bundles one CSV resource per election, each row a
single polling station. We discover resources with ``package_show`` and download
the CSV directly (CKAN also exposes ``datastore_search`` for resources that have
the DataStore enabled; the direct CSV is the most reliable across elections).

These functions need outbound access to ``data.gov.il``. In a restricted sandbox
they raise ``requests`` connection errors — run them where the host is reachable.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd
import requests

from .config import CKAN_BASE, RESULTS_DATASET_ID

_TIMEOUT = 60


@dataclass(frozen=True)
class ResultResource:
    id: str
    name: str
    url: str
    fmt: str


def list_result_resources(dataset_id: str = RESULTS_DATASET_ID) -> list[ResultResource]:
    """Return the downloadable resources in the results dataset."""
    resp = requests.get(
        f"{CKAN_BASE}/package_show", params={"id": dataset_id}, timeout=_TIMEOUT
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN package_show failed: {payload}")
    resources = payload["result"]["resources"]
    return [
        ResultResource(
            id=r.get("id", ""),
            name=r.get("name") or r.get("description") or r.get("id", ""),
            url=r.get("url", ""),
            fmt=(r.get("format") or "").upper(),
        )
        for r in resources
    ]


def _read_csv_bytes(content: bytes) -> pd.DataFrame:
    """Parse CSV bytes, trying the encodings the committee has used over time."""
    for encoding in ("utf-8-sig", "utf-8", "cp1255", "iso-8859-8"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Last resort: let pandas decide and replace bad bytes.
    return pd.read_csv(io.BytesIO(content), encoding="utf-8", encoding_errors="replace")


def fetch_results_csv(url: str) -> pd.DataFrame:
    """Download and parse a per-kalpi result CSV from its resource URL."""
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return _read_csv_bytes(resp.content)


def load_results_csv(path: str) -> pd.DataFrame:
    """Load a per-kalpi result CSV from a local file (same encoding fallback)."""
    with open(path, "rb") as fh:
        return _read_csv_bytes(fh.read())
