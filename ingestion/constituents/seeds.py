"""Read and write constituent seed CSV files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.paths import seed_path

SEED_COLUMNS = ("market_code", "ticker", "company_name", "refreshed_at", "source")


def load_constituents(market_code: str) -> pd.DataFrame:
    path = seed_path(market_code)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing seed file for {market_code}: {path}. "
            "Run scripts/refresh_constituents.py or scripts/import_constituents.py."
        )

    frame = pd.read_csv(path, dtype={"ticker": str})
    missing = [col for col in SEED_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")

    return frame[list(SEED_COLUMNS)].copy()


# A trailing Wikipedia marker: an interlanguage link (`[es]`), a numeric or lowercase-lettered
# footnote (`[1]`, `[a]`), or a named one (`[note 1]`, `[nb 2]`). Applied repeatedly, because
# these tables emit chains (`[es][1]`).
#
# LOWERCASE letters only, and that is the load-bearing decision. Wikipedia writes interlanguage
# links as lowercase ISO 639-1 codes and footnotes as digits or lowercase letters, while an
# UPPERCASE bracketed token of the same length is usually meaningful: `[A]` and `[B]` are Nordic
# share classes, and `[SA]`, `[NV]`, `[AB]`, `[ASA]` are legal forms. Four of the six queued
# markets are named on the share-class convention. Stripping those would merge two constituents
# to one headline, and `write_constituents` de-duplicates on ticker rather than name, so both
# rows would survive as two cards reading identically. An uppercase marker therefore survives
# here ON PURPOSE and is caught instead by the wider seed guard in
# `tests/ingestion/test_market_onboarding.py`, which fails and asks a human, rather than by this
# function, which would silently rewrite a name.
_SCRAPE_MARKER = re.compile(r"\s*\[(?:\d{1,3}|[a-z]{1,3}|(?:note|nb)\s*\d{1,3})\]\s*$")
# Zero-width characters vanish; the exotic spaces collapse to an ordinary one. Wikipedia emits
# U+00A0 constantly and U+202F/U+2009 in numeric and abbreviation contexts.
_INVISIBLE = {ord(c): "" for c in "​‌‍⁠﻿"}
_ODD_SPACE = {ord(c): " " for c in "      "}


def _clean_company_name(names: pd.Series) -> pd.Series:
    """Strip scrape artifacts from a company name before it becomes card copy.

    `company_name` is not an internal field: `dim_stock` prefers the seed name over yfinance's
    `info_long_name`, and the card renders it as the headline. So a Wikipedia marker reaches the
    reader. `Laboratorios Rovi [es]` shipped that way from the IBEX 35 table, preceded by a
    non-breaking space, and nothing caught it.

    Deliberately bounded rather than greedy, and lowercase-only: see the pattern's own comment
    for why an uppercase bracketed token is left alone. Stripping every trailing bracket would
    truncate a real name, which is the worse failure. An artifact that survives is visible and
    gets fixed; a name silently rewritten is not, and two names rewritten to the same string
    become two cards with one headline that nothing downstream can tell apart.
    `tests/ingestion/test_constituent_seeds.py` pins both directions, and the seed guard in
    `test_market_onboarding.py` scans a WIDER set than this strips, in all three of its halves
    (brackets, non-bracket footnote markers, whitespace), so it fails on artifact classes this
    deliberately does not touch. The marker half is the widest of the three relative to this
    function, which strips no non-bracket marker at all.

    What it does NOT do: fix a name that is wrong rather than dirty. The SMI table gives legal
    names ("Novartis International AG") where every other source gives trade names ("Adidas"),
    and no amount of cleaning reconciles that. See the contract.
    """
    cleaned = names.astype(str).str.translate({**_INVISIBLE, **_ODD_SPACE})
    # Loop, not a `+` repeat, so each pass re-anchors on the new end of the string.
    for _ in range(4):
        stripped = cleaned.str.replace(_SCRAPE_MARKER, "", regex=True)
        if stripped.equals(cleaned):
            break
        cleaned = stripped
    return cleaned.str.strip()


def write_constituents(
    market_code: str,
    tickers: pd.Series,
    company_names: pd.Series,
    *,
    source: str,
    refreshed_at: datetime | None = None,
) -> Path:
    refreshed = refreshed_at or datetime.now(timezone.utc)
    frame = pd.DataFrame(
        {
            "market_code": market_code,
            "ticker": tickers.astype(str).str.strip(),
            "company_name": _clean_company_name(company_names),
            "refreshed_at": refreshed.isoformat(),
            "source": source,
        }
    )
    frame = frame.dropna(subset=["ticker"])
    frame = frame[frame["ticker"] != ""]
    frame = frame.drop_duplicates(subset=["ticker"], keep="first")

    path = seed_path(market_code)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path
