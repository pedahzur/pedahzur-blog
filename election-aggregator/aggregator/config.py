"""Configuration and constants for the election aggregator.

Two public data sources are used:

1. data.gov.il (CKAN) — official per-polling-station ("קלפי") Knesset results.
2. Wikipedia — the aggregated opinion-poll tables, one page per election.

NOTE ON NETWORK: some sandboxed environments block these hosts at the egress
proxy. The fetch modules will then fail with a clear connection error; run them
from a machine that can reach ``data.gov.il`` and ``en.wikipedia.org``.
"""

from __future__ import annotations

# --- data.gov.il CKAN ----------------------------------------------------
CKAN_BASE = "https://data.gov.il/api/3/action"
RESULTS_DATASET_ID = "votes-knesset"

# --- Wikipedia -----------------------------------------------------------
# One page per legislative election. Extend as new elections are added.
WIKIPEDIA_POLL_PAGES = {
    2026: "Opinion polling for the 2026 Israeli legislative election",
    2022: "Opinion polling for the 2022 Israeli legislative election",
    2021: "Opinion polling for the 2021 Israeli legislative election",
    2020: "Opinion polling for the 2020 Israeli legislative election",
}
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# --- Result CSV schema ---------------------------------------------------
# The per-kalpi CSVs published by the Central Elections Committee use Hebrew
# headers that vary slightly between elections. We map every known spelling to
# a canonical key so downstream code is schema-stable.
METADATA_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "settlement_name": ("שם ישוב", "שם_ישוב", "שם היישוב", "ישוב"),
    "settlement_code": ("סמל ישוב", "סמל_ישוב", "סמל היישוב"),
    "ballot": ("קלפי", "מספר קלפי", "מספר_קלפי", "קלפי מספר"),
    "ballot_serial": ("ברזל", "מספר ברזל", "מספר_ברזל"),
    "eligible": ("בזב", "בעלי זכות בחירה"),
    "voters": ("מצביעים",),
    "invalid": ("פסולים",),
    "valid": ("כשרים",),
}

# Columns that are metadata, never party-vote columns. Built from the aliases.
_NON_PARTY_COLUMNS: set[str] = {
    alias for aliases in METADATA_COLUMN_ALIASES.values() for alias in aliases
}

# --- Seat allocation (Bader-Ofer / d'Hondt) ------------------------------
KNESSET_SEATS = 120
# Electoral threshold: 3.25% of valid votes since the 2015 election.
ELECTORAL_THRESHOLD = 0.0325
