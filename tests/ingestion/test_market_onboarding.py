"""Onboarding invariants for every active market.

Activating a market touches seven places: the registry, a constituent source config, a
generated seed CSV, dbt's own var list, a `public.markets` row in a Supabase migration, and the
two frontend maps that name the market and give it an exchange suffix.
Miss one and the result is usually not a crash. It is a market that ingests nothing, or an
export that dies on a foreign key during the next scheduled production run with every CI check
green beforehand. These pin the joins between all seven so a half-onboarded market fails at
merge-request time instead. One of them, the dbt var list, is also gated by
`scripts/check_registry_var_sync.py` in CI; the rest have no other guard.

The parametrised tests read `docs/market_registry.yml` at collection time, which is what makes
them track the registry rather than a hardcoded list. The trade: a malformed registry aborts
the whole pytest session with a collection error rather than one failure. That fails closed,
which is right, but it does hide other results behind it.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest
import yaml

from ingestion.constituents.seeds import load_constituents
from ingestion.yfinance.symbols import to_yfinance_ticker

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "docs" / "market_registry.yml"
SOURCES = REPO / "docs" / "constituent_sources.yml"
SEEDS = REPO / "storage" / "seeds"
DBT_PROJECT = REPO / "dbt_analytics" / "dbt_project.yml"
MIGRATIONS = REPO / "supabase" / "migrations"

# Companies that legitimately sit in more than one index and therefore resolve to the same
# Yahoo symbol under two markets. Each entry needs a reason, because the default assumption
# for a repeated symbol is a copy-paste error in a seed, not a real dual listing.
KNOWN_DUAL_INDEX_SYMBOLS: dict[str, tuple[frozenset[str], str]] = {
    "AIR.PA": (
        frozenset({"de_dax", "fr_cac40"}),
        "Airbus is a constituent of both the DAX and the CAC 40, and both indices track its "
        "primary Paris line. The seeds are correct; the deck shows it twice when browsing all "
        "markets, which is a display concern rather than a data one (issue #7).",
    ),
    "MT.AS": (
        frozenset({"fr_cac40", "nl_aex"}),
        "ArcelorMittal is a constituent of both the CAC 40 and the AEX, and both index pages "
        "give its Amsterdam line rather than a Paris one, so the two seeds agree by fact and "
        "not by copying. The deck shows ArcelorMittal THREE times, not two: the IBEX 35 seed "
        "carries its Madrid line as MTS.MC. This guard is keyed on the resolved Yahoo "
        "symbol, so a third listing under a different symbol is invisible to it. Issue #7 "
        "covers the display fix.",
    ),
}


# Wider than the writer strips, in all THREE halves, on purpose: see the guard's docstring.
# An earlier version listed the same eleven code points the writer strips, which made the
# whitespace half able only to confirm the writer's own assumptions. `[^\S ]` is every
# character Python treats as whitespace except the ordinary space, so it covers the Zs block
# the writer does not touch (U+2000 to U+200A, U+205F, U+3000, U+1680) as well as tabs and
# newlines; the second alternative adds the zero-width format characters, which are not
# whitespace to `re`.
_SUSPECT_TRAILING_BRACKET = re.compile(r"\[[^\]]{1,20}\]\s*$")
# Non-bracket footnote markers. Wikipedia uses these alongside bracketed ones, and the
# writer handles neither. Widening the GUARD costs nothing, because it only ever fails and
# asks a human; widening the WRITER on a guess is the over-stripping failure it avoids.
# Deliberately not `[^\w\s]$`: a real name can end in a full stop ("Amazon.com, Inc.").
#
# The superscript digits are split across two blocks and the first version of this class got it
# wrong: `\u2070-\u209f` holds superscript zero and four upwards, while ONE, TWO and THREE are
# U+00B9, U+00B2 and U+00B3 in Latin-1 Supplement. Footnotes number from 1, so the three most
# likely markers were exactly the three it missed. Nothing caught that, because nothing
# exercised the regex; `test_seed_guard_catches_non_bracket_markers` does now.
_SUSPECT_TRAILING_MARKER = re.compile(
    r"[*\u2020\u2021\u00a7\u2016\u00b6\u00b9\u00b2\u00b3\u2070-\u209f\u203b\u2042\u204e]\s*$"
)
_SUSPECT_SPACE = re.compile(r"[^\S ]|[​-‍⁠﻿᠎]")


# Two rows in one seed whose `company_name` is identical. The deck renders both as separate
# cards with the same headline, and nothing downstream distinguishes them. Each entry needs a
# reason, and "known defect" is a reason to fix it, not to accept it.
# Keyed on the PUNCTUATION-INSENSITIVE name, because two headlines that differ only by full
# stops are indistinguishable to a reader and the exact-match version of this guard missed a live
# wrong-company card for that reason. The count is part of the value on purpose: keyed on the
# name alone, an entry would also silence a THIRD row acquiring that name later, which is a new
# defect wearing an old excuse.
KNOWN_DUPLICATE_SEED_NAMES: dict[str, dict[str, tuple[int, str]]] = {
    "jp_nikkei225": {
        "mitsuiosklines": (
            2,
            "DEFECT, pre-existing since the 2026-05-23 import, NOT introduced by market "
            "onboarding, and worse than the Asahi one below. Ticker 9104 is Mitsui O.S.K. "
            "Lines; ticker 9101 is Nippon Yusen (NYK Line) and carries Mitsui's name. So a live "
            "card shows NYK Line's financials under a competitor's name, Nippon Yusen appears "
            "nowhere in the deck, and the two headlines differ only by full stops. Found only "
            "when this guard was widened past exact matching. Recorded in "
            ".claude/active_work.md and filed for its own branch, since fixing it edits a "
            "shipped card headline."
        ),
        "asahigroupholdings": (
            2,
            "DEFECT, pre-existing since the 2026-05-23 import, NOT introduced by market "
            "onboarding. Ticker 2502 is Asahi Group Holdings; ticker 3407 is Asahi Kasei and "
            "carries the wrong name. Whether both rows cleared eligibility in the last run is "
            "not checkable from the repo, so the live effect is either two cards sharing a "
            "headline or one card naming Asahi Kasei as Asahi Group Holdings. Pinned here so it "
            "cannot spread silently, and "
            "recorded in .claude/active_work.md so the record outlives this task's contract. "
            "Fixing it edits a shipped card headline, a section 6 call, so it belongs on its "
            "own branch."
        ),
    },
}


def _headline_key(name: str) -> str:
    """Two names that render as the same headline to a reader.

    Every character outside `[a-z0-9]` is dropped, so that is punctuation, whitespace AND
    accented or non-Latin letters, which is more aggressive than "punctuation" suggests. Enough
    to see "Mitsui O.S.K. Lines" against "Mitsui OSK Lines", and deliberately not enough to merge
    "News Corp (Class A)" with "(Class B)" or "Alphabet Inc. (Class A)" with "(Class C)", which
    are genuinely different securities a reader can tell apart.

    The accent deletion is a theoretical false-merge risk ("L'Oreal" and a hypothetical "Loral"
    in one seed) and inert today: an NFKD accent-folding variant finds exactly the same
    collisions across all nine seeds. Both guards using this key fail loudly and ask a human, so
    the failure direction is safe either way.

    Two guards share this key, which does not make it under-pinned once the live defects are
    fixed: both allowlists are themselves keyed in normalised form, so narrowing the key breaks
    their lookups regardless of what the seeds happen to contain.
    """
    return re.sub(r"[^a-z0-9]+", "", name.casefold())


# The same COMPANY under two markets, resolving to two different Yahoo symbols. This is the
# class `KNOWN_DUAL_INDEX_SYMBOLS` structurally cannot see: it keys on the resolved symbol, so
# Shell as `SHEL.L` and `SHELL.AS` looks like two companies to it. The deck shows one card per
# row either way, so the reader meets the same company twice.
#
# Matching uses `_headline_key`, the same punctuation-insensitive key as the within-market
# guard, and NOT a legal-form-stripping fuzzy matcher. A fuzzy one merges "APA Corporation" (US
# oil and gas) with "APA Group" (Australian gas pipelines), and "Merck" in de_dax (Merck KGaA)
# with "Merck & Co." in us_sp500, which have been unrelated since a 1917 expropriation. Those
# are the merges worth refusing: a missed duplicate is a display flaw, a merged pair asserts two
# companies are one.
#
# Dropping punctuation costs none of that and closes a real gap. An earlier exact-match version
# could not see "News Corp (Class B)" against "News Corp Class B", one company spelled two ways,
# so it was counted in the contract's issue #7 figures while being unrecordable here.
#
# THE LIST BELOW IS STILL A FLOOR, NOT A TOTAL, for two reasons that remain. A company whose two
# seeds differ by more than punctuation (an abbreviation, a suffix one source carries and the
# other does not) stays invisible. And the whole SAME-MARKET class is out of scope by
# construction: Alphabet, Fox and News Corp each ship two share classes inside `us_sp500`, which
# is a different guard's territory and a different decision.
KNOWN_CROSS_MARKET_COMPANIES: dict[str, tuple[frozenset[str], str]] = {
    "airbus": (
        frozenset({"de_dax", "fr_cac40"}),
        "Both indices track the same Paris line, so this one IS symbol-visible and is also in "
        "KNOWN_DUAL_INDEX_SYMBOLS. Listed here so the two allowlists do not disagree.",
    ),
    "arcelormittal": (
        frozenset({"fr_cac40", "nl_aex", "es_ibex35"}),
        "Three cards. The CAC 40 and AEX both give the Amsterdam line (MT.AS, symbol-visible); "
        "the IBEX 35 gives the Madrid line (MTS.MC), which is not.",
    ),
    "shellplc": (
        frozenset({"uk_ftse100", "nl_aex"}),
        "Single share class since the 2022 unification, listed in London and Amsterdam. "
        "SHEL.L and SHELL.AS are two venues for one company. Added by the NL onboarding.",
    ),
    "unilever": (
        frozenset({"uk_ftse100", "nl_aex"}),
        "Single share class since the 2020 unification. ULVR.L and UNA.AS are one company. "
        "Added by the NL onboarding.",
    ),
    "relx": (
        frozenset({"uk_ftse100", "nl_aex"}),
        "Single share class since the 2018 unification. REL.L and REN.AS are one company. "
        "Added by the NL onboarding.",
    ),
    "internationalairlinesgroup": (
        frozenset({"uk_ftse100", "es_ibex35"}),
        "Spanish-incorporated, primary listing London, secondary Madrid. uk_ftse100 carries the "
        "bare ticker IAG (resolving to IAG.L) and es_ibex35 carries IAG.MC, so the resolved "
        "symbols differ and the symbol-keyed guard is blind to the pair. Added by the ES "
        "onboarding.",
    ),
    "amcor": (
        frozenset({"us_sp500", "au_asx200"}),
        "PRE-EXISTING, not added here. Dual-listed; AMCR and AMC.AX are one company.",
    ),
    "newmont": (
        frozenset({"us_sp500", "au_asx200"}),
        "PRE-EXISTING. Dual-listed since the Newcrest acquisition; NEM and NEM.AX are one.",
    ),
    "resmed": (
        frozenset({"us_sp500", "au_asx200"}),
        "PRE-EXISTING. Dual-listed; RMD and RMD.AX are one company.",
    ),
    "blockinc": (
        frozenset({"us_sp500", "au_asx200"}),
        "PRE-EXISTING in the seeds. The raw au_asx200 seed still says XYX (that is what "
        "Wikipedia's own S&P/ASX 200 table lists; not a scrape bug), so "
        "ingestion/constituents/ticker_overrides.csv corrects it to XYZ before any fetch, "
        "fixed 2026-08-29. Once real ingestion next runs for au_asx200, this becomes a genuine "
        "cross-market duplicate like Amcor, Newmont, ResMed and Rio Tinto elsewhere in this "
        "allowlist, not counted as one in the contract before that.",
    ),
    "newscorpclassb": (
        frozenset({"us_sp500", "au_asx200"}),
        "PRE-EXISTING. us_sp500 spells it 'News Corp (Class B)' and au_asx200 spells it "
        "'News Corp Class B': one company, two venues, and invisible to an exact-match version "
        "of this guard, which is why the key drops punctuation. Note News Corp ALSO ships two "
        "share classes inside us_sp500, so it carries three cards in total.",
    ),
    "riotinto": (
        frozenset({"uk_ftse100", "au_asx200"}),
        "PRE-EXISTING. A dual-listed company structure: Rio Tinto plc and Rio Tinto Limited are "
        "separate legal entities sharing one economic interest, so unlike the others this pair "
        "is arguably two valid rows. A reader still meets Rio Tinto twice.",
    ),
}


def _normalised_company_names() -> dict[str, set[str]]:
    """Headline key -> the active markets whose seed carries a company rendering to it.

    Uses `_headline_key`, so two seeds spelling one company differently only in punctuation are
    seen as the same company. See the comment on `KNOWN_CROSS_MARKET_COMPANIES` for why nothing
    beyond punctuation is stripped.
    """
    by_name: dict[str, set[str]] = {}
    for market in _active():
        code = market["market_code"]
        if not _seed_path(code).exists():
            continue
        for row in _seed_rows(code):
            by_name.setdefault(_headline_key(row["company_name"]), set()).add(code)
    return by_name


def test_no_unrecorded_company_appears_under_two_markets() -> None:
    """A company in two indices ships two cards, and the symbol guard cannot see most of them.

    `test_no_symbol_appears_under_two_markets` keys on the resolved Yahoo symbol, which catches
    only the case where both indices track the same listing (Airbus). A company listed on two
    venues resolves to two symbols and slips through: Shell, Unilever, RELX and IAG all did,
    unnoticed for six review rounds, while the contract escalated ArcelorMittal alone to the
    owner as if it were the only instance. News Corp then slipped through an exact-match version
    of THIS guard, which is why it keys on `_headline_key`.

    This does not fail the build for a real dual listing. It fails for an UNRECORDED one, so a
    NEW duplicate cannot arrive unnoticed. It does not enumerate every existing one: see the
    comment on the allowlist for the spelled-two-ways case it structurally cannot hold.
    """
    offenders = []
    for name, markets in _normalised_company_names().items():
        if len(markets) < 2:
            continue
        recorded = KNOWN_CROSS_MARKET_COMPANIES.get(name)
        if recorded is None:
            offenders.append(f"{name!r} in {sorted(markets)}")
        elif recorded[0] != markets:
            offenders.append(
                f"{name!r} recorded for {sorted(recorded[0])}, found {sorted(markets)}"
            )
    assert not offenders, (
        "company appears under more than one market without a recorded reason: "
        + "; ".join(offenders)
    )


def test_cross_market_company_allowlist_has_no_stale_entries() -> None:
    """An entry for a company that is no longer in two markets is a stale excuse. Delete it."""
    found = _normalised_company_names()
    stale = [
        f"{name!r} is now only in {sorted(found.get(name, set()))}"
        for name in KNOWN_CROSS_MARKET_COMPANIES
        if len(found.get(name, set())) < 2
    ]
    assert not stale, "; ".join(stale)


def test_symbol_and_company_allowlists_agree() -> None:
    """Every market PAIR in the symbol allowlist must also appear in the company allowlist.

    Scoped deliberately, because an earlier docstring here claimed more than the code checks:
    this compares market-pair sets, so a new symbol entry landing on a pair another company
    already covers passes without a company entry of its own. Company IDENTITY is pinned
    separately by `test_known_dual_index_symbols_are_all_still_collisions`, which fails if an
    allowlisted symbol stops colliding, so the gap is covered rather than open.
    """
    by_symbol_markets = {
        markets for markets, _reason in KNOWN_DUAL_INDEX_SYMBOLS.values()
    }
    by_name_markets = {
        markets for markets, _reason in KNOWN_CROSS_MARKET_COMPANIES.values()
    }
    missing = [
        sorted(m) for m in by_symbol_markets
        if not any(m <= n for n in by_name_markets)
    ]
    assert not missing, f"symbol allowlist has market pairs the company allowlist lacks: {missing}"


def _registry() -> list[dict]:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["markets"]


def _active() -> list[dict]:
    return [m for m in _registry() if m.get("ingest_active")]


def _active_codes() -> list[str]:
    return [m["market_code"] for m in _active()]


def _sources() -> dict:
    return yaml.safe_load(SOURCES.read_text(encoding="utf-8")).get("markets", {})


def _seed_path(market_code: str) -> Path:
    return SEEDS / market_code / "constituents.csv"


def _seed_rows(market_code: str) -> list[dict]:
    with _seed_path(market_code).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("market_code", _active_codes())
def test_seed_company_names_are_unique_within_a_market(market_code: str) -> None:
    """Two constituents with one headline are indistinguishable on the deck.

    This is the failure mode over-stripping produces, so the guard exists whether or not the
    cleaner ever causes it: `write_constituents` de-duplicates on ticker, never on name, so a
    source table that repeats a name and a cleaner that collapses two names look identical from
    here. It also catches the plain case of a mis-transcribed name, which is what it finds twice
    in the Nikkei seed.

    Matching is punctuation-insensitive, and that is load-bearing rather than tidy: the exact
    version of this guard passed the `9101` row, whose headline differs from `9104`'s only by
    full stops while carrying a different company's financials. It is still not a proof of
    uniqueness. Two rows naming genuinely different companies, one of them wrongly, look correct
    from here as long as the strings differ, which is exactly how the Asahi row survives.
    """
    if not _seed_path(market_code).exists():
        pytest.skip("covered by test_active_market_has_a_constituent_seed")
    allowed = KNOWN_DUPLICATE_SEED_NAMES.get(market_code, {})
    tickers_by_name: dict[str, list[str]] = {}
    for row in _seed_rows(market_code):
        tickers_by_name.setdefault(_headline_key(row["company_name"]), []).append(row["ticker"])
    offenders = []
    for name, tickers in tickers_by_name.items():
        if len(tickers) < 2:
            continue
        permitted = allowed.get(name, (1, ""))[0]
        if len(tickers) > permitted:
            offenders.append(f"{name!r}: {', '.join(tickers)}")
    assert not offenders, (
        f"{market_code} seed gives two companies the same card headline: {'; '.join(offenders)}"
    )


def test_known_duplicate_seed_names_have_not_been_fixed_behind_the_allowlist() -> None:
    """An allowlist entry for a defect that no longer exists is a stale excuse. Delete it."""
    stale = []
    for market_code, names in KNOWN_DUPLICATE_SEED_NAMES.items():
        if not _seed_path(market_code).exists():
            continue
        counts: dict[str, int] = {}
        for row in _seed_rows(market_code):
            key = _headline_key(row["company_name"])
            counts[key] = counts.get(key, 0) + 1
        for name, (permitted, _reason) in names.items():
            if counts.get(name, 0) < permitted:
                stale.append(
                    f"{market_code}: {name!r} appears {counts.get(name, 0)} times, "
                    f"allowlisted for {permitted}"
                )
    assert not stale, "; ".join(stale)


def _strip_sql_comments(sql: str) -> str:
    """Remove `--` and `/* */` comments before scanning.

    Without this the scan passes on a commented-out INSERT, and on a rollback migration whose
    trailing comment quotes the statement it undid. A guard that accepts a commented-out row is
    worse than no guard, because it reads as coverage.
    """
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def _market_codes_in_migrations() -> set[str]:
    """Market codes inserted into `public.markets` by any migration.

    Text-scanned rather than executed: these run against a real Postgres, and the point here is
    only whether the repo would ever create the row. The scan is deliberately conservative and
    fails closed, so it can reject a valid-but-unusual migration: `market_code` must be the
    first column in the VALUES tuple, which the activation checklist states. It is not a SQL
    parser, so a code appearing in a parenthesised literal elsewhere in an INSERT block (say a
    `not in ('fr_cac40')` predicate) would satisfy it.
    """
    codes: set[str] = set()
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = _strip_sql_comments(path.read_text(encoding="utf-8"))
        for block in re.findall(
            r"insert\s+into\s+public\.markets\b(.*?)(?:;|\Z)", sql, re.S | re.I
        ):
            # Only the first literal of each VALUES tuple is a market code. Matching every
            # quoted token would also capture the source column ('yfinance'). The delimiter
            # after it may be a comma or the closing paren, since market_code is not
            # necessarily followed by another column.
            codes.update(re.findall(r"\(\s*'([a-z0-9_]+)'\s*[,)]", block))
    return codes


def _markets_insert_values() -> dict[str, tuple[str, str, str]]:
    """market_code -> (index_name, exchange_suffix, source) as written in the migrations.

    Only reads the four-leading-literal shape the activation checklist prescribes; a migration
    written another way simply yields nothing here and is caught by the row-exists guard.
    """
    found: dict[str, tuple[str, str, str]] = {}
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = _strip_sql_comments(path.read_text(encoding="utf-8"))
        for block in re.findall(
            r"insert\s+into\s+public\.markets\b(.*?)(?:;|\Z)", sql, re.S | re.I
        ):
            for code, index_name, suffix, source in re.findall(
                r"\(\s*'([a-z0-9_]+)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'", block
            ):
                found[code] = (index_name, suffix, source)
    return found


def _markets_by_resolved_symbol() -> dict[str, set[str]]:
    """Resolved Yahoo symbol -> the active markets whose seed produces it.

    Upper-cased because Yahoo symbols are case-insensitive but a seed is only as consistent as
    its source table. Without this, `or.pa` in one seed and `OR.PA` in another read as two
    different companies and the collision guard misses them. Wikipedia sources happen to be
    uppercase today; the TSX 60 and FTSE MIB tables are not yet known to be.
    """
    by_symbol: dict[str, set[str]] = {}
    for market in _active():
        code = market["market_code"]
        if not _seed_path(code).exists():
            continue
        for row in _seed_rows(code):
            symbol = to_yfinance_ticker(row["ticker"], market["exchange_suffix"]).upper()
            by_symbol.setdefault(symbol, set()).add(code)
    return by_symbol


def test_at_least_one_market_is_active() -> None:
    # Load-bearing. pytest turns an empty parametrize set into a SKIP, so without this an
    # emptied registry would read as green-with-skips rather than as a failure.
    assert _active_codes()


def test_market_display_names_hold_no_market_that_is_not_active() -> None:
    """The converse of the per-market display-name check, and it guards a user-facing claim.

    The overflow menu's "About the data" panel derives its coverage line from the cards actually
    in the deck, not from this map, so a name added early cannot overstate coverage there. It
    would still mislabel the market filter. Kept one-line cheap because the failure is silent.
    """
    from markets import MARKET_DISPLAY_NAMES

    extra = set(MARKET_DISPLAY_NAMES) - set(_active_codes())
    assert not extra, f"display names for markets that are not ingest_active: {sorted(extra)}"


@pytest.mark.parametrize("market_code", _active_codes())
def test_active_market_has_a_constituent_seed(market_code: str) -> None:
    path = _seed_path(market_code)
    assert path.exists(), f"{market_code} is ingest_active but has no constituent seed"
    assert _seed_rows(market_code), f"{market_code}'s constituent seed is empty"


@pytest.mark.parametrize("market_code", _active_codes())
def test_seed_rows_carry_their_own_market_code(market_code: str) -> None:
    # A seed copied from another market keeps the original's market_code and would ingest
    # under the wrong partition, which nothing downstream would flag.
    if not _seed_path(market_code).exists():
        pytest.skip("covered by test_active_market_has_a_constituent_seed")
    for row in _seed_rows(market_code):
        assert row["market_code"] == market_code, (
            f"{market_code} seed contains a row labelled {row['market_code']!r}"
        )
        assert row["ticker"].strip(), f"{market_code} seed has a row with no ticker"


@pytest.mark.parametrize("market_code", _active_codes())
def test_active_market_has_a_constituent_source_or_is_declared_manual(market_code: str) -> None:
    """Every active market either refreshes from a configured source or says in writing that
    its seed is maintained by hand. Silence means someone forgot the config, and the seed then
    goes stale with no way to tell that from a market that is deliberately manual."""
    config = _sources().get(market_code)
    assert config is not None, f"{market_code} is ingest_active but has no constituent source"
    if config.get("provider") == "manual":
        assert config.get("notes"), f"{market_code} is manual but does not say how it is updated"
    else:
        for field in ("url", "table_index", "ticker_column", "name_column"):
            assert field in config, f"{market_code} source config is missing {field}"


@pytest.mark.parametrize("market_code", _active_codes())
def test_active_market_has_a_supabase_markets_row(market_code: str) -> None:
    """The join that breaks production rather than CI.

    `mart_stock_cards`, `user_interactions` and `card_assessments` all foreign-key to
    `public.markets`. `export_to_supabase.py` writes the mart only and never inserts a market,
    so a missing row makes the single `replace_cards_snapshot` transaction raise a foreign-key
    violation, which aborts the export for EVERY market and stops the assessment step running.
    No CI job exercises the production export, so nothing else catches this before a scheduled
    run.
    """
    assert market_code in _market_codes_in_migrations(), (
        f"{market_code} is ingest_active but no migration inserts it into public.markets. "
        f"Add one (see supabase/migrations/014_fr_cac40_market.sql) or the next production "
        f"export fails on a foreign key for every market."
    )


def test_no_two_markets_resolve_to_the_same_yahoo_symbol() -> None:
    """Two markets resolving one symbol means one Yahoo record is fetched twice and shipped as
    two near-identical cards, plus a duplicate LLM call. Usually that is a seed copied wrong.
    Occasionally it is a real dual-index constituent, which has to be named and justified in
    KNOWN_DUAL_INDEX_SYMBOLS rather than silently tolerated.
    """
    markets_by_symbol = _markets_by_resolved_symbol()
    collisions: list[str] = []
    for symbol, markets in sorted(markets_by_symbol.items()):
        if len(markets) < 2:
            continue
        allowed = KNOWN_DUAL_INDEX_SYMBOLS.get(symbol, (frozenset(), ""))[0]
        # Exempt only the market pair that was actually justified. An allowlist keyed on the
        # symbol alone would disarm the guard for that symbol in every market, including one
        # where its presence would be plainly wrong.
        if not markets <= allowed:
            collisions.append(f"{symbol}: {', '.join(sorted(markets))}")
    assert not collisions, (
        "Resolved Yahoo symbols collide across markets: "
        + "; ".join(collisions)
        + ". If this is a real dual-index constituent, add it to KNOWN_DUAL_INDEX_SYMBOLS "
        "with the exact set of markets and the reason; otherwise a seed is wrong."
    )


@pytest.mark.parametrize("market_code", _active_codes())
def test_seed_has_no_duplicate_resolved_symbols(market_code: str) -> None:
    """The cross-market guard cannot see a duplicate inside ONE market.

    Keyed on the RESOLVED symbol, not the raw ticker: `AC` and `AC.PA` are different strings in
    the seed but both become `AC.PA`, so a raw-string check would miss the duplicate while
    ingestion fetched Accor twice and shipped two cards. That is the same "seed copied wrong"
    class the cross-market guard exists for, arriving from inside a single file.
    """
    if not _seed_path(market_code).exists():
        pytest.skip("covered by test_active_market_has_a_constituent_seed")
    suffix = {m["market_code"]: m["exchange_suffix"] for m in _active()}[market_code]
    symbols = [
        to_yfinance_ticker(row["ticker"], suffix).upper() for row in _seed_rows(market_code)
    ]
    duplicates = sorted({s for s in symbols if symbols.count(s) > 1})
    assert not duplicates, (
        f"{market_code} seed resolves more than one row to: {', '.join(duplicates)}"
    )


def test_every_active_market_is_named_and_suffixed_in_the_frontend() -> None:
    """The two joins the activation checklist requires and nothing else pins.

    A missing `MARKET_DISPLAY_NAMES` entry does not fail: `market_display_name` falls back to
    title-casing the code, so the filter silently reads "Fr Cac40". A missing `_EXCHANGE_SUFFIX`
    entry is inert only while every one of that market's seed tickers already carries a dot,
    which is true for France and not guaranteed for the markets still queued.
    """
    # Imported, not text-matched: a substring check over the file would be satisfied by the
    # market code appearing in a comment, which is exactly the state this guards against.
    from live_quote import _EXCHANGE_SUFFIX
    from markets import MARKET_DISPLAY_NAMES

    missing_names = [c for c in _active_codes() if c not in MARKET_DISPLAY_NAMES]
    missing_suffixes = [c for c in _active_codes() if c not in _EXCHANGE_SUFFIX]
    assert not missing_names, (
        f"frontend/markets.py MARKET_DISPLAY_NAMES is missing {missing_names}; the market "
        f"filter would render the raw code title-cased."
    )
    assert not missing_suffixes, (
        f"frontend/live_quote.py _EXCHANGE_SUFFIX is missing {missing_suffixes}."
    )


def test_known_dual_index_symbols_are_all_still_collisions() -> None:
    """Stops the allowlist rotting into a list of excuses.

    Checks that each entry still describes a live collision between exactly the markets it
    names, not merely that somebody still seeds the symbol. An entry whose second market
    dropped the constituent is no longer a dual listing, and leaving it behind silently
    pre-authorises the next real collision on that symbol.
    """
    markets_by_symbol = _markets_by_resolved_symbol()
    for symbol, (markets, _reason) in KNOWN_DUAL_INDEX_SYMBOLS.items():
        actual = markets_by_symbol.get(symbol, set())
        assert len(actual) >= 2, (
            f"{symbol} is allowlisted as a dual-index constituent but is now seeded by "
            f"{sorted(actual) or 'no active market'}. Remove the entry."
        )
        assert actual == set(markets), (
            f"{symbol} is allowlisted for {sorted(markets)} but is actually seeded by "
            f"{sorted(actual)}. Update the entry to the markets that really carry it."
        )


def test_dbt_active_markets_match_the_registry() -> None:
    """A second, faster copy of `scripts/check_registry_var_sync.py`.

    That script gates the same invariant in CI on every merge request. This one exists so the
    check also fires in a local `pytest` run, alongside the assertions above that have no
    equivalent anywhere. dbt reads its partition list from `dbt_project.yml`, not the registry,
    so activating a market without syncing leaves dbt ignoring it entirely.
    """
    project = yaml.safe_load(DBT_PROJECT.read_text(encoding="utf-8"))
    dbt_codes = sorted(project["vars"]["active_market_codes"])
    assert dbt_codes == sorted(_active_codes()), (
        "dbt_project.yml is out of sync with the registry. "
        "Run: python scripts/sync_dbt_vars.py"
    )


def test_registry_entries_declare_every_required_field() -> None:
    required = ("market_code", "index_name", "exchange_suffix", "source", "ingest_active")
    for market in _registry():
        for field in required:
            assert field in market, f"{market.get('market_code')} is missing {field}"


@pytest.mark.parametrize("market_code", _active_codes())
def test_supabase_markets_row_matches_the_registry(market_code: str) -> None:
    """Reference data that nothing currently reads is exactly the kind that goes quietly wrong.

    `public.markets` carries index_name, exchange_suffix and source alongside the code. No
    application path reads them today, so a typo there would surface only when something
    eventually does. Each remaining onboarding hand-writes one of these rows.
    """
    registry = {m["market_code"]: m for m in _registry()}[market_code]
    values = _markets_insert_values().get(market_code)
    if values is None:
        pytest.skip("covered by test_active_market_has_a_supabase_markets_row")
    index_name, exchange_suffix, source = values
    assert index_name == registry["index_name"], (
        f"{market_code}: migration says index_name {index_name!r}, "
        f"registry says {registry['index_name']!r}"
    )
    assert exchange_suffix == registry["exchange_suffix"], (
        f"{market_code}: migration says exchange_suffix {exchange_suffix!r}, "
        f"registry says {registry['exchange_suffix']!r}"
    )
    assert source == registry["source"], (
        f"{market_code}: migration says source {source!r}, registry says {registry['source']!r}"
    )


@pytest.mark.parametrize("market_code", _active_codes())
def test_seed_company_names_carry_no_scrape_artifacts(market_code: str) -> None:
    """`company_name` is card copy, not an internal field.

    `dim_stock` prefers the seed name over yfinance's `info_long_name`, and the card renders it
    as the headline, so a Wikipedia interlanguage marker reaches the reader. `Laboratorios Rovi
    [es]` shipped that way from the IBEX 35 table, preceded by a non-breaking space, and nothing
    caught it: CI never reads real seeds, because the fixture seeder synthesises its own names.
    `ingestion.constituents.seeds` strips these at write time now; this pins the outcome for a
    hand-edited or imported seed too.
    The patterns below are deliberately WIDER than the ones `_clean_company_name` strips, in all
    three halves: brackets, non-bracket markers, and whitespace. A guard built from the
    writer's own regex can only confirm the writer's assumptions,
    so it would pass on exactly the artifact classes the writer overlooks. This one fails on any
    short trailing bracket, including the uppercase tokens the writer leaves alone on purpose,
    and on any whitespace character other than an ordinary space. It can therefore fire on a
    legitimate name: a real `[Holding]` suffix, or a Nordic share class written `[B]`. That is the
    intended direction. A false alarm is a human decision; a missed artifact is a wrong card
    headline, and a silently over-stripped name is two cards that read the same.
    """
    if not _seed_path(market_code).exists():
        pytest.skip("covered by test_active_market_has_a_constituent_seed")
    offenders = []
    for row in _seed_rows(market_code):
        name = row["company_name"]
        if (
            _SUSPECT_TRAILING_BRACKET.search(name)
            or _SUSPECT_TRAILING_MARKER.search(name)
            or _SUSPECT_SPACE.search(name)
        ):
            offenders.append(f"{row['ticker']}: {name!r}")
        elif not name.strip() or name.strip().lower() == "nan":
            offenders.append(f"{row['ticker']}: empty or null name")
    assert not offenders, (
        f"{market_code} seed carries scrape artifacts in company_name: {'; '.join(offenders)}"
    )


def test_ci_baseline_covers_every_active_market() -> None:
    """`scripts/eligibility_baseline.ci.json` is maintained by hand at checklist step 11.

    Forgetting it fails OPEN on the aggregate side: the per-market floor of 5 still binds, but
    the total stops matching and the drop gate loses the new market's contribution. The fixture
    seeder writes a fixed 7 rows per active market, so both the membership and the arithmetic
    are checkable from here.
    """
    baseline = json.loads((REPO / "scripts" / "eligibility_baseline.ci.json").read_text("utf-8"))
    markets = baseline["markets"]
    active = set(_active_codes())
    assert set(markets) == active, (
        f"ci baseline markets {sorted(set(markets) ^ active)} differ from the active registry"
    )
    total = sum(m["baseline_eligible"] for m in markets.values())
    assert baseline["total_baseline_eligible"] == total, (
        f"total_baseline_eligible {baseline['total_baseline_eligible']} != sum of markets {total}"
    )
    # The fixture seeder writes a fixed 7 rows per active market, so every entry must be 7. A
    # hand-typed lower number keeps the total self-consistent while quietly shrinking that
    # market's share of the aggregate drop check.
    wrong = {
        code: m["baseline_eligible"]
        for code, m in markets.items()
        if m["baseline_eligible"] != 7
    }
    assert not wrong, f"ci fixtures produce 7 eligible per market; baseline says {wrong}"


def test_the_seed_guard_stays_wider_than_the_writer() -> None:
    """The guard's whole value is catching what `_clean_company_name` deliberately skips.

    An earlier version of `_SUSPECT_SPACE` listed exactly the eleven code points the writer
    strips, which made this half of the guard a restatement of the writer's own assumptions: it
    could only ever confirm them. Nothing pinned the relationship, so a future edit could narrow
    it back silently. This asserts the containment directly rather than trusting a comment.
    """
    from ingestion.constituents.seeds import _INVISIBLE, _ODD_SPACE

    writer_strips = set(_INVISIBLE) | set(_ODD_SPACE)
    missed = [hex(cp) for cp in sorted(writer_strips) if not _SUSPECT_SPACE.search(chr(cp))]
    assert not missed, f"guard no longer catches what the writer strips: {missed}"
    wider = [
        cp for cp in range(0x3100)
        if _SUSPECT_SPACE.search(chr(cp)) and cp not in writer_strips
    ]
    assert len(wider) >= 20, (
        f"guard has narrowed to {len(wider)} code points beyond the writer's set; it is supposed "
        "to be materially wider so it can fail on classes the writer does not handle"
    )


# (marker, should_the_guard_fire). The superscripts are the point: an earlier version of the
# class held only U+2070 and up, so the three commonest footnote markers passed silently.
_MARKER_CASES = [
    ("Acme Corp*", True),
    ("Acme Corp\u2020", True),
    ("Acme Corp\u2021", True),
    ("Acme Corp\u00a7", True),
    ("Acme Corp\u00b6", True),
    ("Acme Corp\u00b9", True),
    ("Acme Corp\u00b2", True),
    ("Acme Corp\u00b3", True),
    ("Acme Corp\u2074", True),
    ("Acme Corp\u2070", True),
    ("Acme Corp\u203b", True),
    ("Acme Corp‖", True),
    ("Acme Corp⁂", True),
    ("Acme Corp⁎", True),
    ("Acme Corp₁", True),
    ("Acme Corp* ", True),
    # Must NOT fire. A trailing full stop is ordinary, which is why the class is an explicit
    # list rather than "any trailing punctuation".
    ("Amazon.com, Inc.", False),
    ("Yum! Brands", False),
    ("Acme Corp", False),
    ("Acme*Corp", False),
    ("L'Oreal", False),
]


@pytest.mark.parametrize("name,should_fire", _MARKER_CASES)
def test_seed_guard_catches_non_bracket_markers(name: str, should_fire: bool) -> None:
    """Pins `_SUSPECT_TRAILING_MARKER`, which nothing exercised when it was added.

    Two reviewers proved that independently: deleting the regex, or replacing it with one that
    never matches, left the whole suite green. A guard no test can distinguish from its own
    absence is not a guard, and this file already learned that once with `_SUSPECT_SPACE`.
    """
    assert bool(_SUSPECT_TRAILING_MARKER.search(name)) is should_fire


def test_seed_guard_bracket_half_catches_more_than_the_writer_strips() -> None:
    """The bracket half must stay wide enough to catch what `_clean_company_name` skips.

    The writer strips only short LOWERCASE markers, deliberately, so uppercase share classes and
    legal forms survive it. This asserts the guard still notices those, which is the whole basis
    for the writer being allowed to be conservative. Narrowing the guard's bound to `{1,3}` would
    otherwise pass every other test in the repo.
    """
    for name in ("Acme [Holding]", "Novo Nordisk [B]", "Equinor [ASA]", "Acme [note 1]"):
        assert _SUSPECT_TRAILING_BRACKET.search(name), f"guard no longer notices {name!r}"


COMPANY_NAME_OVERRIDES = REPO / "dbt_analytics" / "seeds" / "company_name_overrides.csv"


def _override_rows() -> list[dict]:
    with COMPANY_NAME_OVERRIDES.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_company_name_overrides_target_real_constituents() -> None:
    """Every override row must correct a ticker that actually exists in the seed it targets.

    This is a plain-file check, not a dbt one, on purpose: CI's `dbt build` runs against a
    synthetic fixture database that seeds every market with the same handful of made-up
    tickers, so a dbt-side test comparing the override against `stg_yf__constituents` would
    report all real tickers as "dead" and fail in CI regardless of whether the override is
    correct. Reading both CSVs directly from disk sidesteps that entirely.

    The failure this catches: a source table renumbers a ticker after the override was
    written, and the override silently corrects nothing while looking like it does.
    """
    offenders = []
    for row in _override_rows():
        market_code = row["market_code"]
        if not _seed_path(market_code).exists():
            offenders.append(f"{market_code}/{row['ticker']}: no such market seed")
            continue
        real_tickers = {r["ticker"] for r in _seed_rows(market_code)}
        if row["ticker"] not in real_tickers:
            offenders.append(
                f"{market_code}/{row['ticker']}: not in the current seed (renumbered or removed?)"
            )
    assert not offenders, "; ".join(offenders)


def test_company_name_overrides_have_no_duplicate_keys() -> None:
    """Two rows for the same (market_code, ticker) is ambiguous: which one does dbt apply?

    The override join in `base_yf__constituents` is a plain left join, not deduped, so a
    duplicate override key would fan out that ticker's row instead of erroring, so this has
    to be caught here rather than relying on dbt to notice.
    """
    seen: dict[tuple[str, str], str] = {}
    dupes = []
    for row in _override_rows():
        key = (row["market_code"], row["ticker"])
        if key in seen:
            dupes.append(f"{key[0]}/{key[1]} appears more than once")
        seen[key] = row["company_name"]
    assert not dupes, "; ".join(dupes)


def test_company_name_overrides_covers_the_audited_nikkei_defects() -> None:
    """Pins the eleven tickers the 2026-08-28 yfinance audit found wrong, so the override
    file can't silently lose a row on a future edit without a test noticing.
    """
    audited_tickers = {
        "3407", "6908", "6976", "8005", "8804",
        "8830", "9005", "9008", "9009", "9101", "9412",
    }
    rows = [r for r in _override_rows() if r["market_code"] == "jp_nikkei225"]
    covered = {r["ticker"] for r in rows}
    assert covered == audited_tickers, (
        f"expected exactly {sorted(audited_tickers)}, found {sorted(covered)}"
    )


def test_company_name_overrides_covers_the_approved_smi_trade_names() -> None:
    """Pins the nineteen tickers the owner approved a trade-name override for on 2026-08-28,
    so the override file can't silently lose a row on a future edit without a test noticing.

    KNIN (Kuehne + Nagel) is deliberately absent: the seed already carries a trade name there.
    """
    approved_tickers = {
        "NOVN", "ROP", "NESN", "ABBN", "UBSG", "CFR", "ZURN", "HOLN", "SREN",
        "LONN", "SCMN", "GIVN", "ALC", "SIKA", "AMRZ", "SLHN", "GEBN", "PGHN", "LOGN",
    }
    rows = [r for r in _override_rows() if r["market_code"] == "ch_smi"]
    covered = {r["ticker"] for r in rows}
    assert covered == approved_tickers, (
        f"expected exactly {sorted(approved_tickers)}, found {sorted(covered)}"
    )


TICKER_OVERRIDES = REPO / "ingestion" / "constituents" / "ticker_overrides.csv"


def _ticker_override_rows() -> list[dict]:
    with TICKER_OVERRIDES.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ticker_overrides_target_real_constituents() -> None:
    """Every override row must correct a ticker that actually exists in the seed it targets.

    Same rationale as `test_company_name_overrides_target_real_constituents`: the failure this
    catches is a source table renumbering or removing a ticker after the override was written,
    leaving the override correcting nothing while looking like it does.
    """
    offenders = []
    for row in _ticker_override_rows():
        market_code = row["market_code"]
        if not _seed_path(market_code).exists():
            offenders.append(f"{market_code}/{row['ticker']}: no such market seed")
            continue
        real_tickers = {r["ticker"] for r in _seed_rows(market_code)}
        if row["ticker"] not in real_tickers:
            offenders.append(
                f"{market_code}/{row['ticker']}: not in the current seed (renumbered or removed?)"
            )
    assert not offenders, "; ".join(offenders)


def test_ticker_overrides_have_no_duplicate_keys() -> None:
    """Two rows for the same (market_code, ticker) is ambiguous: which correction applies?

    `_apply_ticker_overrides` builds a plain dict from `zip(ticker, corrected_ticker)`, so a
    duplicate key would silently let the last row win instead of erroring.
    """
    seen: dict[tuple[str, str], str] = {}
    dupes = []
    for row in _ticker_override_rows():
        key = (row["market_code"], row["ticker"])
        if key in seen:
            dupes.append(f"{key[0]}/{key[1]} appears more than once")
        seen[key] = row["corrected_ticker"]
    assert not dupes, "; ".join(dupes)


def test_ticker_overrides_covers_the_known_au_asx200_defect() -> None:
    """Pins the one ticker correction approved on 2026-08-29, so it can't silently disappear."""
    rows = [r for r in _ticker_override_rows() if r["market_code"] == "au_asx200"]
    assert [r["ticker"] for r in rows] == ["XYX"]
    assert rows[0]["corrected_ticker"] == "XYZ"


def test_load_constituents_applies_the_au_asx200_ticker_override() -> None:
    """End-to-end proof against the real files on disk, not a synthetic fixture.

    The raw seed still says XYX (matching Wikipedia's own table); this proves the override
    mechanism actually fires today and the yfinance fetch list would carry the correct ticker,
    not just that `ticker_overrides.csv` has the right row in isolation.
    """
    constituents = load_constituents("au_asx200")
    block_rows = constituents[constituents["company_name"].str.contains("Block", na=False)]
    assert len(block_rows) == 1, f"expected exactly one Block row, found {len(block_rows)}"
    assert block_rows.iloc[0]["ticker"] == "XYZ"
