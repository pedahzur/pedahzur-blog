"""Command-line interface for the election aggregator.

Examples
--------
    # List the per-election CSV resources available on data.gov.il
    python -m aggregator.cli list-results

    # Aggregate a result CSV to settlement level + national seat allocation
    python -m aggregator.cli results --url <csv-url> --year 2022 --out data/

    # Same, from a previously downloaded file
    python -m aggregator.cli results --local data/knesset25.csv --year 2022 --out data/

    # Download the Wikipedia poll table for an election
    python -m aggregator.cli polls --year 2022 --out data/
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from . import aggregate, parties, polls, results


def _cmd_list_results(args: argparse.Namespace) -> None:
    for r in results.list_result_resources():
        print(f"{r.fmt:5}  {r.name}\n        {r.url}")


def _load_result_frame(args: argparse.Namespace) -> pd.DataFrame:
    if args.local:
        return results.load_results_csv(args.local)
    if args.url:
        return results.fetch_results_csv(args.url)
    raise SystemExit("provide --url or --local")


def _cmd_results(args: argparse.Namespace) -> None:
    df = _load_result_frame(args)

    by_settlement = aggregate.aggregate_by_settlement(df)
    totals = aggregate.national_totals(df)
    seats = aggregate.bader_ofer(totals)
    seats_named = parties.rename_to_party_names(seats, args.year)

    print(f"Polling stations: {len(df):,}  Settlements: {len(by_settlement):,}")
    print(f"National valid votes (sum over parties): {int(totals.sum()):,}\n")
    print("Seat allocation (Bader-Ofer):")
    for name, s in seats_named.items():
        print(f"  {s:3d}  {name}")
    print(f"  ---  total {int(seats_named.sum())}")

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        by_settlement.to_csv(os.path.join(args.out, f"settlements_{args.year}.csv"), index=False)
        totals.to_csv(os.path.join(args.out, f"national_votes_{args.year}.csv"))
        seats_named.to_csv(os.path.join(args.out, f"seats_{args.year}.csv"))
        print(f"\nWrote settlement/national/seat CSVs to {args.out}")


def _cmd_polls(args: argparse.Namespace) -> None:
    table = polls.extract_polls(args.year)
    print(f"Parsed {len(table)} poll rows, {table.shape[1]} columns")
    print(table.head(10).to_string())
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, f"polls_{args.year}.csv")
        table.to_csv(path, index=False)
        print(f"\nWrote {path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aggregator", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("list-results", help="list result CSV resources on data.gov.il")
    sp.set_defaults(func=_cmd_list_results)

    sp = sub.add_parser("results", help="aggregate a per-kalpi result CSV")
    sp.add_argument("--url", help="CKAN resource URL of the per-kalpi CSV")
    sp.add_argument("--local", help="path to a local per-kalpi CSV")
    sp.add_argument("--year", type=int, required=True, help="election year (for party names)")
    sp.add_argument("--out", help="output directory for aggregated CSVs")
    sp.set_defaults(func=_cmd_results)

    sp = sub.add_parser("polls", help="scrape the Wikipedia poll table")
    sp.add_argument("--year", type=int, required=True)
    sp.add_argument("--out", help="output directory for the polls CSV")
    sp.set_defaults(func=_cmd_polls)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
