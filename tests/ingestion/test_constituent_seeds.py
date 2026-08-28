"""Unit tests for the constituent seed writer.

`test_market_onboarding.py` pins the OUTCOME: no committed seed carries a scrape artifact. That
guard is one-sided by construction. It fails when the cleaner strips too little, and passes when
the cleaner strips too much, because an over-stripped name is still a clean name. Over-stripping
is the worse failure of the two: it silently rewrites a company's headline. These pin the cleaner
itself, from both directions.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ingestion.constituents.seeds import _clean_company_name

# Names that must survive untouched. The bracketed entries are the load-bearing ones: they are
# what stops the pattern being widened to `\[[^\]]*\]$`, which would truncate them while leaving
# every other test in the repo green.
PRESERVED = [
    "Kuehne + Nagel",
    "Nestlé SA",
    "Compagnie Financière Richemont SA",
    "Schneider Electric SE",
    "Guess ?, Inc.",
    "Fomento de Construcciones y Contratas",
    "Berkshire Hathaway (Class B)",
    "Compagnie Financiere Richemont [Holding]",
    "Moller-Maersk [A/S]",
    "Amundi ETF [Europe] SA",
    "Anheuser-Busch InBev",
    "L'Oreal",
    "Aena [es] SME SA",
    "BE Semiconductors",
    # Uppercase bracketed tokens survive ON PURPOSE. These are Nordic share classes and legal
    # forms, not Wikipedia markers, and four of the six queued markets are named on that
    # convention. An uppercase footnote is caught by the wider seed guard instead, which asks a
    # human rather than silently merging two constituents into one headline.
    "Novo Nordisk [B]",
    "Atlas Copco [A]",
    "Equinor [ASA]",
    "Volvo [AB]",
    "Telefonica [SA]",
    "Bank [NV]",
]

# (raw, expected). The first is the payload actually observed in the IBEX 35 table.
STRIPPED = [
    ("\u00a0Laboratorios Rovi [es]", "Laboratorios Rovi"),
    ("Laboratorios Rovi [es]", "Laboratorios Rovi"),
    ("Solaria Energia [1]", "Solaria Energia"),
    ("Some Company [a]", "Some Company"),
    ("Some Company [note 1]", "Some Company"),
    ("Some Company [nb 2]", "Some Company"),
    ("Chained Co [es][1]", "Chained Co"),
    ("Acciona\u00a0SA", "Acciona SA"),
    ("Ferrovial\u202fSE", "Ferrovial SE"),
    ("Ferrovial\u200bSE", "FerrovialSE"),
    ("  Iberdrola SA  ", "Iberdrola SA"),
]


@pytest.mark.parametrize("name", PRESERVED)
def test_clean_company_name_preserves_real_names(name: str) -> None:
    """A real name is card copy. Silently rewriting one is worse than leaving an artifact in."""
    assert _clean_company_name(pd.Series([name])).iloc[0] == name


@pytest.mark.parametrize("raw,expected", STRIPPED)
def test_clean_company_name_strips_scrape_artifacts(raw: str, expected: str) -> None:
    assert _clean_company_name(pd.Series([raw])).iloc[0] == expected


def test_clean_company_name_strips_only_a_trailing_marker() -> None:
    """Mid-string brackets are not markers. Wikipedia footnotes sit at the end of the cell."""
    assert _clean_company_name(pd.Series(["Aena [es] SME SA"])).iloc[0] == "Aena [es] SME SA"


def test_clean_company_name_is_vectorised_over_the_series() -> None:
    out = _clean_company_name(pd.Series(["A [es]", "B", "\u00a0C"]))
    assert list(out) == ["A", "B", "C"]


def test_clean_company_name_does_not_invent_a_name_for_a_null() -> None:
    """A null name must stay null, never become the literal string "nan" on a card headline.

    This holds because pandas 3 preserves NA through `astype(str)`; on pandas 2 the same
    expression yields "nan". `requirements.txt` pins 3.0.3, so the test also fails loudly if that
    pin is ever relaxed backwards, which is the point of asserting it rather than assuming it.
    """
    for null in (None, float("nan"), pd.NA):
        assert pd.isna(_clean_company_name(pd.Series([null])).iloc[0])
