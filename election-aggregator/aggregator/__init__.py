"""Israel election poll aggregator.

Pulls official per-kalpi Knesset results from data.gov.il and aggregated opinion
polls from Wikipedia, then compares projected vs actual Knesset seats.
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import aggregate, compare, normalize, parties, polls, results  # noqa: F401
