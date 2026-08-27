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
import re
from pathlib import Path

import pytest
import yaml

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
}


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
    so a missing row makes the first batch containing that market raise a foreign-key
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
    eventually does. Nine more onboardings will each hand-write one of these rows.
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
