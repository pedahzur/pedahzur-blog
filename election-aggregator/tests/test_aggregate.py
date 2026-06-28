import os

import pandas as pd
import pytest

from aggregator import aggregate, compare, normalize, results

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_kalpi.csv")


@pytest.fixture
def raw():
    return results.load_results_csv(FIXTURE)


def test_identify_party_columns(raw):
    party_cols = normalize.identify_party_columns(raw)
    assert set(party_cols) == {"מחל", "פה", "שס", "אמת"}
    # turnout / metadata columns must not be classified as parties
    for meta in ("בזב", "מצביעים", "פסולים", "כשרים", "סמל ישוב"):
        assert meta not in party_cols


def test_standardize_metadata_columns(raw):
    std = normalize.standardize_metadata_columns(raw)
    for key in ("settlement_name", "settlement_code", "ballot", "eligible", "valid"):
        assert key in std.columns


def test_aggregate_by_settlement(raw):
    by_settlement = aggregate.aggregate_by_settlement(raw)
    assert len(by_settlement) == 3  # Tel Aviv, Jerusalem, Haifa
    tlv = by_settlement.set_index("settlement_code").loc[5000]
    assert tlv["מחל"] == 150 + 160
    assert tlv["פה"] == 120 + 130
    assert tlv["valid"] == 395 + 400


def test_national_totals(raw):
    totals = aggregate.national_totals(raw)
    assert totals["מחל"] == 150 + 160 + 300 + 310 + 180
    assert totals["אמת"] == 100 + 80 + 32 + 30 + 74
    # sorted descending
    assert list(totals.index)[0] == "מחל"


def test_bader_ofer_simple_dhondt():
    # 100 seats, two parties 60/40 -> 60/40 by d'Hondt
    seats = aggregate.bader_ofer({"A": 60000, "B": 40000}, seats=100, threshold=0.0)
    assert seats["A"] == 60
    assert seats["B"] == 40
    assert int(seats.sum()) == 100


def test_bader_ofer_threshold_drops_small_party():
    votes = {"A": 50000, "B": 47000, "C": 2000}  # C ~2% < 3.25%
    seats = aggregate.bader_ofer(votes, seats=10, threshold=0.0325)
    assert "C" not in seats.index
    assert int(seats.sum()) == 10


def test_bader_ofer_surplus_agreement_pools_votes():
    # Without an agreement the last seat is contested; pooling A+B should win it.
    votes = {"A": 33000, "B": 33000, "C": 34000}
    no_pool = aggregate.bader_ofer(votes, seats=7, threshold=0.0)
    pooled = aggregate.bader_ofer(
        votes, seats=7, threshold=0.0, surplus_agreements=[("A", "B")]
    )
    assert int(no_pool.sum()) == 7
    assert int(pooled.sum()) == 7
    # The pooled bloc captures at least as many seats as the parties did apart.
    assert pooled["A"] + pooled["B"] >= no_pool["A"] + no_pool["B"]


def test_compare_seats_mae():
    projected = {"Likud": 32, "Yesh Atid": 24, "Meretz": 5}
    actual = {"Likud": 32, "Yesh Atid": 24, "Meretz": 0, "Shas": 11}
    df = compare.compare_seats(projected, actual)
    assert df.loc["Meretz", "error"] == 5  # projected 5, won 0
    assert df.loc["Shas", "error"] == -11  # missed entirely
    assert df.attrs["total_abs_error"] == 16
    assert df.attrs["mae"] == pytest.approx(16 / 4)
