"""Mapping between official ballot letter-codes (the result-CSV headers) and the
party display names used in the Wikipedia poll tables.

Letter-codes (אותיות) are reused and reassigned over time, so this map is keyed
by election year. Only the codes needed to line up polls with results are listed;
extend per election as needed. Names are kept close to the English Wikipedia
poll-table column labels so the comparison join is direct.
"""

from __future__ import annotations

# year -> {ballot_code: display_name}
BALLOT_CODE_TO_NAME: dict[int, dict[str, str]] = {
    2022: {
        "מחל": "Likud",
        "פה": "Yesh Atid",
        "ט": "Religious Zionism",
        "כן": "National Unity",  # ha-Mahane ha-Mamlachti
        "שס": "Shas",
        "ג": "United Torah Judaism",
        "ל": "Yisrael Beiteinu",
        "עם": "Ra'am",
        "ום": "Hadash-Ta'al",
        "אמת": "Labor",
        "מרצ": "Meretz",
        "ב": "Yamina",
        "ודעם": "Balad",
    },
    2021: {
        "מחל": "Likud",
        "פה": "Yesh Atid",
        "ב": "Yamina",
        "שס": "Shas",
        "ג": "United Torah Judaism",
        "ל": "Yisrael Beiteinu",
        "ט": "Religious Zionism",
        "כן": "Blue and White",
        "עם": "Ra'am",
        "אמת": "Labor",
        "מרצ": "Meretz",
        "ום": "Joint List",
        "ת": "New Hope",
    },
}


def code_to_name(year: int, code: str) -> str:
    """Return the display name for a ballot code, or the code itself if unknown."""
    return BALLOT_CODE_TO_NAME.get(year, {}).get(code, code)


def rename_to_party_names(votes, year: int):
    """Re-index a votes/seats Series from ballot codes to display names.

    Unknown codes are kept verbatim so nothing is silently dropped.
    """
    return votes.rename(lambda code: code_to_name(year, code))
