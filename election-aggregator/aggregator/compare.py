"""Compare projected seats from polls against the actual seat allocation.

Polls are national-level only (no kalpi/settlement breakdown exists for polls),
so the comparison is by party at the national level: for each party we line up
the poll's projected seats with the seats actually won.
"""

from __future__ import annotations

import pandas as pd


def compare_seats(
    projected: pd.Series | dict[str, float],
    actual: pd.Series | dict[str, int],
) -> pd.DataFrame:
    """Return a per-party comparison of projected vs actual seats.

    Both inputs are keyed by the same party names. Parties present in only one
    side are kept with 0 on the missing side, so dropped/new parties are visible.
    Columns: ``projected``, ``actual``, ``error`` (projected - actual),
    ``abs_error``. The frame carries ``.attrs['mae']`` and ``.attrs['total_abs_error']``.
    """
    projected = pd.Series(dict(projected), dtype="float64")
    actual = pd.Series(dict(actual), dtype="float64")

    parties = sorted(set(projected.index) | set(actual.index))
    df = pd.DataFrame(
        {
            "projected": projected.reindex(parties).fillna(0.0),
            "actual": actual.reindex(parties).fillna(0.0),
        }
    )
    df["error"] = df["projected"] - df["actual"]
    df["abs_error"] = df["error"].abs()
    df = df.sort_values("actual", ascending=False)

    df.attrs["mae"] = float(df["abs_error"].mean()) if len(df) else 0.0
    df.attrs["total_abs_error"] = float(df["abs_error"].sum())
    return df


def pollster_accuracy(
    polls: pd.DataFrame,
    actual: pd.Series | dict[str, int],
    party_columns: list[str],
    pollster_column: str = "Polling firm",
) -> pd.DataFrame:
    """Rank pollsters by mean absolute seat error against the actual result.

    ``polls`` is the tidy table from :func:`aggregator.polls.extract_polls`;
    ``party_columns`` lists the columns in it that hold projected seats (their
    names must match the keys in ``actual``). One row per pollster, averaged over
    that pollster's polls, sorted from most to least accurate.
    """
    actual = pd.Series(dict(actual), dtype="float64")
    rows = []
    for pollster, group in polls.groupby(pollster_column):
        abs_errors = []
        for party in party_columns:
            if party not in actual.index:
                continue
            projected = pd.to_numeric(group[party], errors="coerce")
            abs_errors.extend((projected - actual[party]).abs().dropna().tolist())
        if abs_errors:
            rows.append(
                {
                    "pollster": pollster,
                    "n_polls": len(group),
                    "mae": sum(abs_errors) / len(abs_errors),
                }
            )
    return pd.DataFrame(rows).sort_values("mae").reset_index(drop=True)
