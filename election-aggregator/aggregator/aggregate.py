"""Aggregate per-kalpi results up to settlement and national level, and
allocate Knesset seats with the Bader-Ofer method.
"""

from __future__ import annotations

import pandas as pd

from .config import ELECTORAL_THRESHOLD, KNESSET_SEATS
from .normalize import (
    coerce_numeric,
    identify_party_columns,
    standardize_metadata_columns,
)


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Normalize a raw result frame and return ``(frame, party_columns)``."""
    party_cols = identify_party_columns(df)
    df = standardize_metadata_columns(df)
    df = coerce_numeric(df, party_cols)
    return df, party_cols


def aggregate_by_settlement(df: pd.DataFrame) -> pd.DataFrame:
    """Sum every numeric column per settlement (יישוב).

    Returns one row per settlement, indexed by ``settlement_code`` when present
    (falling back to ``settlement_name``), keeping party votes and any turnout
    counts (eligible/voters/valid/invalid) that exist in the frame.
    """
    df, party_cols = prepare(df)

    if "settlement_code" in df.columns:
        group_keys = ["settlement_code"]
        if "settlement_name" in df.columns:
            group_keys.append("settlement_name")
    elif "settlement_name" in df.columns:
        group_keys = ["settlement_name"]
    else:
        raise ValueError("frame has no settlement column to group by")

    turnout_cols = [c for c in ("eligible", "voters", "invalid", "valid") if c in df.columns]
    sum_cols = turnout_cols + party_cols
    for col in turnout_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    grouped = df.groupby(group_keys, as_index=False)[sum_cols].sum()
    return grouped


def national_totals(df: pd.DataFrame) -> pd.Series:
    """Return a Series mapping party column -> total national votes."""
    df, party_cols = prepare(df)
    totals = df[party_cols].sum().astype("int64")
    totals.name = "votes"
    return totals.sort_values(ascending=False)


def bader_ofer(
    votes: pd.Series | dict[str, int],
    seats: int = KNESSET_SEATS,
    threshold: float = ELECTORAL_THRESHOLD,
    surplus_agreements: list[tuple[str, str]] | None = None,
) -> pd.Series:
    """Allocate ``seats`` using the Bader-Ofer (largest-averages / d'Hondt) method.

    Parties below ``threshold`` (share of total valid votes) are dropped first.
    ``surplus_agreements`` is a list of party pairs (heskemei odafim) that pool
    their votes for the allocation, then split the pooled seats between them by a
    second d'Hondt round — the real Israeli rule. Pass ``None`` to ignore them
    (a close approximation that is exact when no pair crosses an apportionment
    boundary).

    Returns a Series mapping party -> seats, descending.
    """
    votes = pd.Series(dict(votes), dtype="int64")
    total = int(votes.sum())
    if total == 0:
        return pd.Series(dtype="int64")

    qualifying = votes[votes / total >= threshold]
    if qualifying.empty:
        return pd.Series(dtype="int64")

    # Build pooled "blocs" for surplus agreements.
    agreements = surplus_agreements or []
    bloc_of: dict[str, str] = {}
    members: dict[str, list[str]] = {}
    for a, b in agreements:
        if a in qualifying.index and b in qualifying.index:
            bloc = f"{a}+{b}"
            bloc_of[a] = bloc
            bloc_of[b] = bloc
            members[bloc] = [a, b]

    bloc_votes: dict[str, int] = {}
    for party, v in qualifying.items():
        bloc = bloc_of.get(party, party)
        bloc_votes[bloc] = bloc_votes.get(bloc, 0) + int(v)

    bloc_seats = _dhondt(bloc_votes, seats)

    # Split each bloc's seats between its two members by a second d'Hondt round.
    result: dict[str, int] = {}
    for bloc, s in bloc_seats.items():
        if bloc in members:
            inner = {m: int(qualifying[m]) for m in members[bloc]}
            for m, ms in _dhondt(inner, s).items():
                result[m] = ms
        else:
            result[bloc] = s

    out = pd.Series(result, dtype="int64").sort_values(ascending=False)
    out.name = "seats"
    return out


def _dhondt(votes: dict[str, int], seats: int) -> dict[str, int]:
    """Pure d'Hondt allocation of ``seats`` across ``votes``."""
    allocation = {p: 0 for p in votes}
    for _ in range(seats):
        # Next seat goes to the party with the highest quotient v / (s + 1).
        winner = max(votes, key=lambda p: votes[p] / (allocation[p] + 1))
        allocation[winner] += 1
    return allocation
