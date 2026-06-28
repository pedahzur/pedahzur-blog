"""Schema normalization for the per-kalpi result CSVs.

The Central Elections Committee publishes one CSV per election. Each row is a
single polling station (קלפי). A handful of leading columns are metadata
(settlement, ballot number, turnout counts); every *other* column is a party,
headed by that party's official Hebrew ballot letters (e.g. ``מחל``, ``פה``,
``אמת``). Those letter-codes are far more stable across elections than party
display names, so we keep them as the party key and map to display names
separately (see :mod:`aggregator.parties`).
"""

from __future__ import annotations

import pandas as pd

from .config import METADATA_COLUMN_ALIASES, _NON_PARTY_COLUMNS


def _strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with whitespace-trimmed column names."""
    return df.rename(columns=lambda c: str(c).strip())


def standardize_metadata_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known Hebrew metadata headers to canonical English keys.

    Unknown columns (i.e. the party columns) are left untouched.
    """
    df = _strip_columns(df)
    rename: dict[str, str] = {}
    for canonical, aliases in METADATA_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                rename[alias] = canonical
                break
    return df.rename(columns=rename)


def identify_party_columns(df: pd.DataFrame) -> list[str]:
    """Return the columns that hold party vote counts.

    A column is a party column when it is not a known metadata column and its
    values are numeric (votes). Works on a frame *before or after*
    :func:`standardize_metadata_columns` because canonical keys are excluded too.
    """
    df = _strip_columns(df)
    canonical_keys = set(METADATA_COLUMN_ALIASES.keys())
    party_cols: list[str] = []
    for col in df.columns:
        if col in _NON_PARTY_COLUMNS or col in canonical_keys:
            continue
        # A party column must be numeric-coercible (votes).
        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.notna().any():
            party_cols.append(col)
    return party_cols


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce the given columns to integer vote counts (NaN -> 0)."""
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
    return df
