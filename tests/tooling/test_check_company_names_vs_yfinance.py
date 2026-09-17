"""Tests for the name-vs-yfinance audit guard (issue #19)."""

from __future__ import annotations

from collections import defaultdict

from check_company_names_vs_yfinance import (
    KNOWN_STYLISTIC_DIVERGENCES,
    _load_name_overrides,
    _load_snapshot,
    _tokenize_company_name,
    final_seed_names,
    find_mismatches,
    names_are_compatible,
)


def test_tokenize_strips_diacritics_and_punctuation() -> None:
    assert _tokenize_company_name("Acciona Energía") == _tokenize_company_name(
        "Acciona Energia"
    )
    assert _tokenize_company_name("A. O. Smith") == _tokenize_company_name("A O Smith")


def test_tokenize_is_case_insensitive() -> None:
    assert _tokenize_company_name("NESTLE SA") == _tokenize_company_name("nestle sa")


def test_tokenize_strips_a_leading_the() -> None:
    assert _tokenize_company_name("The Coca-Cola Company") == _tokenize_company_name(
        "Coca-Cola Company"
    )


def test_tokenize_strips_a_trailing_parenthetical() -> None:
    """Wikipedia's alphabetization convention ("Home Depot (The)" sorts under H) and a
    share-class qualifier ("News Corp (Class B)") both need to fall away before comparing,
    since yfinance's longName reflects neither -- found running this guard for real."""
    assert _tokenize_company_name("Home Depot (The)") == _tokenize_company_name("Home Depot")
    assert _tokenize_company_name("News Corp (Class B)") == _tokenize_company_name("News Corp")


def test_tokenize_collapses_a_dotted_abbreviation_but_not_a_compound_word() -> None:
    """Found running this guard for real against a live yfinance snapshot (issue #19):
    a blanket "period between two letters" rule fuses "Amazon.com" into one token
    ("amazoncom"), breaking its prefix match against the seed's own "Amazon". Restricting
    the collapse to runs of single-letter-then-period groups ("S.A.", "K.K.") avoids that."""
    assert _tokenize_company_name("Nestle S.A.") == _tokenize_company_name("Nestle SA")
    # "Amazon.com" is NOT collapsed -- "n" and "c" are not single-letter tokens, so the
    # dotted-abbreviation rule doesn't apply, and "amazon" still prefix-matches.
    assert _tokenize_company_name("Amazon.com, Inc.") == ["amazon", "com", "inc"]
    assert names_are_compatible("Amazon", "Amazon.com, Inc.") is True


def test_names_are_compatible_when_one_is_a_leading_prefix_of_the_other() -> None:
    assert names_are_compatible("BlueScope", "BlueScope Steel Limited") is True
    assert names_are_compatible("Commonwealth Bank", "Commonwealth Bank of Australia") is True


def test_names_are_compatible_false_when_they_diverge_within_the_shared_length() -> None:
    """The remaining real-divergence class this guard exists to catch: two names that
    start similarly, or not at all, but are not actually a prefix relationship."""
    assert names_are_compatible("Downer Group", "Downer EDI Limited") is False
    assert names_are_compatible("Munich Re", "Münchener Rückversicherungs-Gesellschaft") is False


def test_names_are_compatible_does_not_conflate_two_different_companies_sharing_a_suffix() -> (
    None
):
    """The false-merge risk this repo's own headline-collision guard already warns about
    (Merck KGaA vs Merck & Co)."""
    assert names_are_compatible("Merck & Co", "Merck KGaA") is False


def test_find_mismatches_flags_a_real_divergence(monkeypatch) -> None:
    import pandas as pd

    monkeypatch.setattr(
        "check_company_names_vs_yfinance.load_constituents",
        lambda market_code: pd.DataFrame(
            [{"ticker": "XYZ", "company_name": "Wrong Company"}]
        ),
    )
    mismatches, missing = find_mismatches(
        ["fake_market"], overrides={}, snapshot={("fake_market", "XYZ"): "Right Company"}
    )
    assert missing == []
    assert len(mismatches) == 1
    assert "Wrong Company" in mismatches[0]
    assert "Right Company" in mismatches[0]


def test_find_mismatches_passes_on_a_stylistic_only_difference(monkeypatch) -> None:
    import pandas as pd

    monkeypatch.setattr(
        "check_company_names_vs_yfinance.load_constituents",
        lambda market_code: pd.DataFrame([{"ticker": "MMM", "company_name": "3M"}]),
    )
    mismatches, missing = find_mismatches(
        ["fake_market"], overrides={}, snapshot={("fake_market", "MMM"): "3M Company"}
    )
    assert mismatches == []
    assert missing == []


def test_find_mismatches_applies_the_name_override(monkeypatch) -> None:
    import pandas as pd

    monkeypatch.setattr(
        "check_company_names_vs_yfinance.load_constituents",
        lambda market_code: pd.DataFrame(
            [{"ticker": "NOVN", "company_name": "Novartis International AG"}]
        ),
    )
    mismatches, missing = find_mismatches(
        ["ch_smi"],
        overrides={("ch_smi", "NOVN"): "Novartis"},
        snapshot={("ch_smi", "NOVN"): "Novartis AG"},
    )
    assert mismatches == []
    assert missing == []


def test_known_stylistic_divergences_are_still_divergent_not_stale() -> None:
    """An allowlist entry whose divergence has quietly resolved (yfinance renamed to
    match) is a stale excuse, exactly the class of check `test_market_onboarding.py`'s own
    `KNOWN_DUPLICATE_SEED_NAMES` staleness test guards against. Reads the real committed
    seeds/overrides/snapshot directly -- run scripts/refresh_yfinance_names.py first if
    this fails because the snapshot doesn't cover an allowlisted ticker yet."""
    overrides = _load_name_overrides()
    snapshot = _load_snapshot()
    by_market: dict[str, list[str]] = defaultdict(list)
    for market_code, ticker in KNOWN_STYLISTIC_DIVERGENCES:
        by_market[market_code].append(ticker)

    stale = []
    for market_code, tickers in by_market.items():
        try:
            names = final_seed_names(market_code, overrides)
        except FileNotFoundError:
            continue
        for ticker in tickers:
            seed_name = names.get(ticker)
            snap_name = snapshot.get((market_code, ticker))
            if seed_name is None or snap_name is None:
                continue  # covered by the "no snapshot entry" warning path, not this test
            if names_are_compatible(seed_name, snap_name):
                stale.append(f"{market_code}:{ticker} no longer diverges -- remove the entry")
    assert not stale, "; ".join(stale)


def test_find_mismatches_warns_not_fails_on_a_missing_snapshot_entry(monkeypatch) -> None:
    import pandas as pd

    monkeypatch.setattr(
        "check_company_names_vs_yfinance.load_constituents",
        lambda market_code: pd.DataFrame([{"ticker": "ABC", "company_name": "Some Co"}]),
    )
    mismatches, missing = find_mismatches(["fake_market"], overrides={}, snapshot={})
    assert mismatches == []
    assert len(missing) == 1
    assert "fake_market:ABC" in missing[0]
