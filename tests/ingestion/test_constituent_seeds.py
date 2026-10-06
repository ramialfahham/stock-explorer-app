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

from ingestion.constituents import seeds
from ingestion.constituents.seeds import _apply_ticker_overrides, _clean_company_name

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


_TICKER_OVERRIDES = pd.DataFrame(
    {
        "market_code": ["au_asx200"],
        "ticker": ["XYX"],
        "corrected_ticker": ["XYZ"],
        "reason": ["test fixture"],
    }
)


def test_apply_ticker_overrides_replaces_a_matching_pair() -> None:
    out = _apply_ticker_overrides(
        "au_asx200", pd.Series(["XYX", "WTC"]), _TICKER_OVERRIDES
    )
    assert list(out) == ["XYZ", "WTC"]


def test_apply_ticker_overrides_ignores_the_same_ticker_in_another_market() -> None:
    """The override is keyed on (market_code, ticker) together, not ticker alone.

    The failure this guards: a join or lookup that matches on ticker only would rewrite an
    unrelated market's identically-spelled ticker, the same collision risk the base-layer
    company-name join guards against.
    """
    out = _apply_ticker_overrides("us_sp500", pd.Series(["XYX"]), _TICKER_OVERRIDES)
    assert list(out) == ["XYX"]


def test_apply_ticker_overrides_is_a_noop_with_no_matching_rows() -> None:
    empty = pd.DataFrame(columns=["market_code", "ticker", "corrected_ticker", "reason"])
    out = _apply_ticker_overrides("au_asx200", pd.Series(["WTC", "XRO"]), empty)
    assert list(out) == ["WTC", "XRO"]


def test_apply_ticker_overrides_is_vectorised_over_the_series() -> None:
    out = _apply_ticker_overrides(
        "au_asx200", pd.Series(["WTC", "XYX", "XRO"]), _TICKER_OVERRIDES
    )
    assert list(out) == ["WTC", "XYZ", "XRO"]


def test_load_ticker_overrides_is_a_noop_for_a_missing_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", tmp_path / "does_not_exist.csv")
    out = seeds._load_ticker_overrides()
    assert list(out.columns) == list(seeds.TICKER_OVERRIDE_COLUMNS)
    assert len(out) == 0


def test_load_ticker_overrides_is_a_noop_for_a_zero_byte_file(tmp_path, monkeypatch) -> None:
    """A file that exists but has no header at all must not crash every market's load.

    `pandas.read_csv` raises `EmptyDataError` on a genuinely empty file, and that error would
    otherwise propagate out of `load_constituents()` unconditionally, before the market filter
    even runs, breaking every market rather than just one with no override.
    """
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", path)
    out = seeds._load_ticker_overrides()
    assert list(out.columns) == list(seeds.TICKER_OVERRIDE_COLUMNS)
    assert len(out) == 0


def test_load_ticker_overrides_raises_a_clear_error_for_the_wrong_columns(
    tmp_path, monkeypatch
) -> None:
    """A renamed or typo'd column must fail loudly at load time, not as a bare KeyError deep
    inside `_apply_ticker_overrides` for whichever market happens to run first.
    """
    path = tmp_path / "wrong_columns.csv"
    path.write_text("market,ticker,corrected,why\nau_asx200,XYX,XYZ,test\n", encoding="utf-8")
    monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", path)
    with pytest.raises(ValueError, match="missing columns"):
        seeds._load_ticker_overrides()


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("OSE: EQNR", "EQNR"),
        ("MAERSK B", "MAERSK-B"),
        ("  NOVO B  ", "NOVO-B"),
        ("NA", "NA"),
        ("CTC.A", "CTC.A"),
        ("ERIC-B.ST", "ERIC-B.ST"),
        ("7203", "7203"),
    ],
)
def test_clean_ticker(raw: str, expected: str) -> None:
    assert seeds._clean_ticker(pd.Series([raw])).tolist() == [expected]


def test_clean_ticker_turns_a_missing_cell_into_an_empty_string() -> None:
    missing = pd.Series([float("nan"), None], dtype=object)
    assert seeds._clean_ticker(missing).tolist() == ["", ""]


def test_write_constituents_drops_a_missing_ticker(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(seeds, "seed_path", lambda code: tmp_path / code / "constituents.csv")
    count = seeds.write_constituents(
        "ca_tsx60",
        pd.Series(["AEM", float("nan"), "NA"], dtype=object),
        pd.Series(["Agnico Eagle", None, "National Bank of Canada"], dtype=object),
        source="wikipedia",
    )
    written = pd.read_csv(tmp_path / "ca_tsx60" / "constituents.csv", na_filter=False)
    assert written["ticker"].tolist() == ["AEM", "NA"]
    assert count == 2


@pytest.mark.parametrize("name", ["", "   ", None, float("nan")])
def test_write_constituents_refuses_a_kept_row_without_a_name(tmp_path, monkeypatch, name) -> None:
    path = tmp_path / "constituents.csv"
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)
    with pytest.raises(ValueError, match="no company name for NA"):
        seeds.write_constituents(
            "ca_tsx60",
            pd.Series(["AEM", "NA"], dtype=object),
            pd.Series(["Agnico Eagle", name], dtype=object),
            source="wikipedia",
        )
    assert not path.exists()


def test_ticker_overrides_match_the_ticker_na(tmp_path, monkeypatch) -> None:
    path = tmp_path / "ticker_overrides.csv"
    path.write_text(
        "market_code,ticker,corrected_ticker,reason\nca_tsx60,NA,NA-X,test\n", encoding="utf-8"
    )
    monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", path)
    overrides = seeds._load_ticker_overrides()
    assert _apply_ticker_overrides("ca_tsx60", pd.Series(["NA"]), overrides).tolist() == ["NA-X"]


def test_load_constituents_keeps_the_ticker_na(tmp_path, monkeypatch) -> None:
    path = tmp_path / "constituents.csv"
    path.write_text(
        "market_code,ticker,company_name,refreshed_at,source\n"
        "ca_tsx60,NA,National Bank of Canada,2026-10-05T00:00:00+00:00,wikipedia\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)
    monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", tmp_path / "does_not_exist.csv")
    assert seeds.load_constituents("ca_tsx60")["ticker"].tolist() == ["NA"]


def test_fetch_wikipedia_table_keeps_the_ticker_na(monkeypatch) -> None:
    from ingestion.constituents import refresh

    html = (
        "<table><tr><th>Symbol</th><th>Company</th></tr>"
        "<tr><td>NA</td><td>National Bank of Canada</td></tr></table>"
    )

    class _Response:
        text = html

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(refresh.requests, "get", lambda *a, **k: _Response())
    table = refresh._fetch_wikipedia_table("https://example.org", 0)
    assert table["Symbol"].tolist() == ["NA"]


def _refresh_with_table(monkeypatch, tmp_path, table: pd.DataFrame, strip_suffix: str | None):
    from ingestion.constituents import refresh

    out = tmp_path / "constituents.csv"
    monkeypatch.setattr(refresh, "_fetch_wikipedia_table", lambda url, index: table)
    monkeypatch.setattr(seeds, "seed_path", lambda code: out)
    config = refresh.RefreshConfig(
        market_code="de_dax", provider="wikipedia", refresh_enabled=True, url="https://example.org",
        table_index=0, ticker_column="Ticker", name_column="Company", strip_suffix=strip_suffix,
    )
    refresh.refresh_market(config)
    return pd.read_csv(out, dtype=str, na_filter=False)["ticker"].tolist()


DAX_PAGE = pd.DataFrame({
    "Ticker": ["ADS.DE", "AIR.PA", "SAP", "BAS.DE ", "X.DEF", None],
    "Company": ["Adidas", "Airbus", "SAP", "BASF", "Made up", None],
}, dtype=object)


def test_refresh_strips_only_the_configured_suffix(monkeypatch, tmp_path) -> None:
    """Only a trailing .DE goes, also behind trailing whitespace (a stray non-breaking space
    must not keep the suffix and re-key the card); .DE inside a ticker stays."""
    assert _refresh_with_table(monkeypatch, tmp_path, DAX_PAGE, ".DE") == [
        "ADS", "AIR.PA", "SAP", "BAS", "X.DEF",
    ]


def test_refresh_without_strip_suffix_keeps_the_page_form(monkeypatch, tmp_path) -> None:
    assert _refresh_with_table(monkeypatch, tmp_path, DAX_PAGE, None) == [
        "ADS.DE", "AIR.PA", "SAP", "BAS.DE", "X.DEF",
    ]


def test_de_dax_keeps_its_committed_bare_ticker_form() -> None:
    """#39: the DAX page writes ADS.DE where the committed seed (and every DAX card key) has
    ADS; without this the next DAX refresh re-keys every card."""
    from ingestion.constituents.refresh import load_refresh_configs

    assert load_refresh_configs()["de_dax"].strip_suffix == ".DE"


def _committed_seed(path, tickers: list[str]) -> None:
    rows = "".join(f"ca_tsx60,{t},Co {t},2026-10-01T00:00:00+00:00,wikipedia\n" for t in tickers)
    header = "market_code,ticker,company_name,refreshed_at,source\n"
    path.write_text(header + rows, encoding="utf-8")


def _write(tickers: list[str], min_overlap: float | None) -> int:
    return seeds.write_constituents(
        "ca_tsx60",
        pd.Series(tickers),
        pd.Series([f"Co {t}" for t in tickers]),
        source="wikipedia",
        min_overlap=min_overlap,
    )


TWENTY = [f"T{i:02d}" for i in range(20)]


def test_refresh_refuses_a_table_that_re_keys_the_committed_seed(tmp_path, monkeypatch) -> None:
    path = tmp_path / "constituents.csv"
    _committed_seed(path, TWENTY)
    before = path.read_bytes()
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)
    with pytest.raises(ValueError, match="only 0% of the committed seed's 20 tickers"):
        _write([f"{t}.TO" for t in TWENTY], min_overlap=0.85)
    assert path.read_bytes() == before


@pytest.mark.parametrize("kept,refused", [(20, False), (17, False), (16, True)])
def test_refresh_overlap_threshold_is_inclusive(tmp_path, monkeypatch, kept, refused) -> None:
    path = tmp_path / "constituents.csv"
    _committed_seed(path, TWENTY)
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)
    new = TWENTY[:kept] + [f"NEW{i}" for i in range(20 - kept)]
    if refused:
        with pytest.raises(ValueError, match="seed not written"):
            _write(new, min_overlap=0.85)
    else:
        assert _write(new, min_overlap=0.85) == 20


def test_overlap_is_not_checked_without_a_minimum_or_a_committed_seed(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "constituents.csv"
    monkeypatch.setattr(seeds, "seed_path", lambda code: path)
    assert _write(TWENTY, min_overlap=0.85) == 20
    assert _write([f"{t}.TO" for t in TWENTY], min_overlap=None) == 20
