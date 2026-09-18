"""Guard: flag a seed company_name that no longer matches yfinance's own company name.

Issue #19. Compares each `provider: wikipedia` market's constituent seed name -- after
`ticker_overrides.csv` and `company_name_overrides.csv` (both `dbt_analytics/seeds/`) are
applied, the same "final" name the card actually renders (see `dim_stock.sql`'s coalesce)
-- against a periodically-refreshed cached snapshot of yfinance's own `info.longName`
(`scripts/refresh_yfinance_names.py`). Catches the class of defect that shipped as 11 wrong
`jp_nikkei225` company names in one session, caught previously only by a one-off manual
script: the two existing seed guards in `tests/ingestion/test_market_onboarding.py` only
fire when the true company's name ALSO happens to collide with another seed row, which
missed 9 of those 11.

`provider: manual` markets (`jp_nikkei225` today) are out of scope: there is no independent
source to compare a hand-curated seed against, so a guard there would just compare the seed
to itself. Scoped to `docs/constituent_sources.yml`'s `provider` field, not the market
registry.

A ticker with no snapshot entry (the snapshot is stale or a market was onboarded since the
last refresh) is a WARNING, not a hard failure -- a different failure class (operational
staleness) from an actual name defect, and failing every PR for an unrelated market's
missing snapshot row would be overly strict.
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.constituents.refresh import load_refresh_configs
from ingestion.constituents.seeds import load_constituents
from ingestion.paths import NAME_OVERRIDES_PATH, NAME_SNAPSHOT_PATH
from ingestion.registry import load_markets

# A leading token to drop before comparing -- "The Coca-Cola Company" must still prefix-match
# "Coca-Cola", and a leading mismatch would otherwise block that regardless of the rest.
_LEADING_SUFFIXES = {"the"}

# A confirmed-correct final name (seed or company_name_overrides.csv) that still diverges
# from yfinance's longName after normalization, because yfinance's own name carries a real,
# distinguishing word -- "International", a "Compagnie Financière" prefix -- that this
# guard's normalizer deliberately never strips (stripping a real word, not a known legal
# suffix, risks the exact false-merge class `test_market_onboarding.py`'s own
# KNOWN_DUPLICATE_SEED_NAMES already warns about). Found by running this guard for real
# against a live yfinance snapshot (issue #19); each entry paired with
# `test_known_stylistic_divergences_are_still_divergent` in this file's test suite, which
# fails if the divergence has quietly resolved (yfinance renamed) or, worse, silently
# changed into a real mismatch -- so a stale entry can't hide behind this allowlist.
KNOWN_STYLISTIC_DIVERGENCES: dict[tuple[str, str], str] = {
    ("ch_smi", "CFR"): "yfinance longName is 'Compagnie Financière Richemont SA' -- not a "
    "prefix relationship with the confirmed trade name 'Richemont' at all, since the legal "
    "name leads with 'Compagnie Financière' instead of the company's own name",
    # Reviewed against the full live snapshot (issue #19): every entry below confirmed as
    # the same company under a trade name / acronym / legal-form divergence prefix
    # matching can't bridge, grouped by market.
    ("au_asx200", "PDI"): "Predictive Discovery Limited officially renamed to PDI Gold "
    "Limited, effective September 2026 (shareholder approval 21 August 2026) -- confirmed "
    "via GlobeNewswire and BNN Bloomberg wire releases, not general knowledge. The seed's "
    "own display name is now stale, a separate follow-up from this guard's own scope",
    ("es_ibex35", "COL.MC"): "Inmobiliaria Colonial completed a cross-border merger "
    "absorbing its subsidiary Société Foncière Lyonnaise (SFL) in 2025, renaming the "
    "merged entity to 'Colonial SFL, SOCIMI, S.A.' -- confirmed via Euronext's own company "
    "news feed and Colonial's own investor-relations site (colonial-sfl.com), not general "
    "knowledge. Same company, seed's display name is stale",
    ("uk_ftse100", "DCC"): "DCC plc renamed to DCC Energy plc -- confirmed via the London "
    "Stock Exchange's own company listing page, not general knowledge. Same company, "
    "seed's display name is stale",
    ("au_asx200", "ANZ"): "seed's 'Australia & New Zealand Banking Group' is what ANZ "
    "stands for; yfinance's 'ANZ Group Holdings Limited' is the same bank under its "
    "2022-23 holding-company restructure -- same entity, not a coincidental acronym match",
    ("au_asx200", "DOW"): "'Downer EDI Limited' is Downer Group's actual ASX-listed legal "
    "name since a 2001 merger with EDI",
    ("au_asx200", "LTR"): "Liontown Resources renamed to Liontown Limited",
    ("au_asx200", "NWS"): "yfinance's longName does not distinguish share classes; both "
    "NWS (Class B) and NWSA (Class A) resolve to plain 'News Corporation'",
    ("au_asx200", "REH"): "'Reece Limited' is the ASX legal name; 'Reece Group' is informal "
    "branding",
    ("au_asx200", "SGM"): "Sims Metal Management renamed to Sims Limited",
    ("au_asx200", "SOL"): "'Soul Patts' is the well-known colloquial short name for "
    "Washington H. Soul Pattinson and Company Limited",
    ("au_asx200", "TNE"): "'TechnologyOne' is a no-space stylization of 'Technology One "
    "Limited'",
    ("de_dax", "BMW"): "'Bayerische Motoren Werke' is literally what BMW stands for",
    ("de_dax", "DHL"): "Deutsche Post rebranded its group entity to DHL Group/DHL AG "
    "around 2023",
    ("de_dax", "HNR1"): "'Re' is the standard English abbreviation for 'Rückversicherung' "
    "(reinsurance); a well-known reinsurer",
    ("de_dax", "MUV2"): "'Munich Re' is the universal trade name for Münchener "
    "Rückversicherungs-Gesellschaft, one of the world's largest reinsurers",
    ("de_dax", "PAH3"): "'Porsche SE' is the short form of 'Porsche Automobil Holding SE', "
    "the holding company (ticker PAH3), distinct from carmaker Porsche AG",
    ("de_dax", "VOW3"): "'Group' vs 'AG', same entity",
    ("es_ibex35", "ANE.MC"): "'Acciona Energía' is the renewable-energy subsidiary of "
    "Acciona; yfinance carries its full legal name",
    ("es_ibex35", "BBVA.MC"): "'Banco Bilbao Vizcaya Argentaria' is literally what BBVA "
    "stands for",
    ("es_ibex35", "IAG.MC"): "'International Airlines Group' is the well-known short form "
    "of 'International Consolidated Airlines Group S.A.' (British Airways/Iberia parent)",
    ("es_ibex35", "ITX.MC"): "'Inditex' is literally an acronym/contraction of 'Industria "
    "de Diseño Textil' -- the same company, parent of Zara",
    ("es_ibex35", "ROVI.MC"): "just missing 'Farmaceuticos' from the legal name, same "
    "company",
    ("es_ibex35", "SAB.MC"): "just missing 'de', same company",
    ("es_ibex35", "SAN.MC"): "'Santander' is the universal trade name for Banco Santander, "
    "S.A.",
    ("fr_cac40", "AI.PA"): "French definite article 'L'' + legal form, same company",
    ("fr_cac40", "ML.PA"): "Michelin's documented formal legal name/structure",
    ("fr_cac40", "SGO.PA"): "'Compagnie de Saint-Gobain S.A.' is the well-known company's "
    "full legal name",
    ("nl_aex", "AD.AS"): "'Koninklijke' (Royal) is the standard Dutch corporate prefix, "
    "same company",
    ("nl_aex", "AKZA.AS"): "spacing only ('AkzoNobel' vs 'Akzo Nobel'), same company",
    ("nl_aex", "BESI.AS"): "'BE Semiconductors' is the common short form of 'BE "
    "Semiconductor Industries N.V.'",
    ("nl_aex", "INGA.AS"): "Dutch 'Groep' vs English 'Group', same company",
    ("nl_aex", "KPN.AS"): "'Koninklijke KPN' (Royal KPN) is the full legal name; KPN "
    "itself is an acronym of 'Koninklijke PTT Nederland'",
    ("nl_aex", "PHIA.AS"): "'Koninklijke' (Royal) is the standard Dutch corporate prefix, "
    "same company",
    ("uk_ftse100", "BBOX"): "'Ord' (ordinary shares) is yfinance's standard abbreviation "
    "for UK investment trusts",
    ("uk_ftse100", "HWDN"): "'Howdens' is the trading/consumer brand; 'Howden Joinery "
    "Group Plc' is the formal legal name",
    ("uk_ftse100", "IAG"): "same as es_ibex35:IAG.MC -- 'International Airlines Group' is "
    "the well-known short form",
    ("uk_ftse100", "IHG"): "'IHG' is literally an acronym of 'InterContinental Hotels "
    "Group'",
    ("uk_ftse100", "PCT"): "'Ord' (ordinary shares) is yfinance's standard abbreviation "
    "for UK investment trusts",
    ("uk_ftse100", "SBRY"): "'Sainsbury's' is the trading name; 'J Sainsbury plc' is the "
    "formal legal name",
    ("uk_ftse100", "SMT"): "'Ord' (ordinary shares) is yfinance's standard abbreviation "
    "for UK investment trusts",
    ("uk_ftse100", "WEIR"): "'Group' vs 'PLC', same company",
    ("us_sp500", "BEN"): "Franklin Resources adopted the 'Franklin Templeton' group brand "
    "name",
    ("us_sp500", "BNY"): "'BNY' is the well-known abbreviation of 'The Bank of New York "
    "Mellon Corporation'",
    ("us_sp500", "DECK"): "'Deckers Brands' is the current trading name; 'Deckers Outdoor "
    "Corporation' is the SEC-registered legal name",
    ("us_sp500", "DHI"): "spaced initials 'D. R.' vs unspaced 'D.R.' -- a normalization gap "
    "this guard's tokenizer doesn't bridge, not a data issue",
    ("us_sp500", "GLW"): "'Inc.' vs 'Incorporated', same word",
    ("us_sp500", "GWW"): "spaced initials 'W. W.' vs unspaced 'W.W.' -- same normalization "
    "gap as us_sp500:DHI",
    ("us_sp500", "IBM"): "'International Business Machines Corporation' is literally what "
    "IBM stands for",
    ("us_sp500", "LLY"): "'(Eli)' is the seed's own alphabetization convention (sorts "
    "under L); 'Eli Lilly and Company' is the same well-known company",
    ("us_sp500", "MRSH"): "shortened form of 'Marsh & McLennan Companies, Inc.', same "
    "company",
    ("us_sp500", "NWS"): "yfinance's longName does not distinguish share classes; both "
    "NWS (Class B) and NWSA (Class A) resolve to plain 'News Corporation'",
    ("us_sp500", "NWSA"): "same as us_sp500:NWS",
    ("us_sp500", "RCL"): "Royal Caribbean Cruises Ltd. rebranded to Royal Caribbean Group "
    "around 2019-2020; yfinance still carries the prior legal name",
    ("us_sp500", "SJM"): "parenthetical placement only, same exact name",
    ("us_sp500", "SLB"): "Schlumberger rebranded to SLB in 2022, a well-known industry "
    "rebrand",
    ("us_sp500", "SMCI"): "'Supermicro' is the commonly used stylization of 'Super Micro "
    "Computer, Inc.'",
    ("us_sp500", "WAB"): "'Wabtec' is an acronym/short form of 'Westinghouse Air Brake "
    "Technologies'",
}


def _tokenize_company_name(name: str) -> list[str]:
    """Diacritic-, punctuation-, and dotted-abbreviation-insensitive token list.

    Deliberately does not casefold-and-strip its way to a single "canonical" name --
    running this guard for real against a live yfinance snapshot (issue #19) found that
    yfinance's `longName` is the full LEGAL name for ~15% of all constituents ("Commonwealth
    Bank" vs "Commonwealth Bank of Australia", "BlueScope" vs "BlueScope Steel Limited"),
    far too systemic and varied for a fixed suffix list to bridge. `names_are_compatible`
    below instead treats one name being a leading token-sequence of the other as a match,
    which covers that whole class without needing to enumerate every legal form in the
    world -- see its own docstring for why this is still conservative enough to avoid a
    false merge."""
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # A trailing parenthetical is Wikipedia's alphabetization convention ("Home Depot
    # (The)" sorts under H, not T) or a share-class qualifier ("News Corp (Class B)") --
    # yfinance's longName reflects neither ("The Home Depot, Inc.", plain "News
    # Corporation" for every class of the same company). Dropped whole, not just "(The)",
    # since it never carries a real distinguishing word for either case.
    text = re.sub(r"\s*\([^)]*\)\s*$", " ", text)
    # "&" must survive as a real token, not vanish as if it were mere whitespace between
    # two adjacent words -- "Merck & Co" would otherwise become indistinguishable from
    # "Merck Co", and a bare prefix check could then treat it as compatible with the
    # unrelated "Merck KGaA" (caught by this file's own test suite).
    text = text.replace("&", " and ")
    # A dotted abbreviation ("S.A.", "A.G.") must collapse to one token, the same as its
    # undotted form ("SA", "AG") -- but ONLY a run of single-LETTER-then-period groups.
    # A blanket "period between two letters" rule also fuses "Amazon.com" into one token
    # ("amazoncom"), which then fails to prefix-match against the seed's own "Amazon" --
    # found the same way, running this guard for real.
    text = re.sub(r"\b(?:[A-Za-z]\.){2,}", lambda m: m.group(0).replace(".", ""), text)
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).casefold()
    tokens = [t for t in text.split() if t]
    while tokens and tokens[0] in _LEADING_SUFFIXES:
        tokens.pop(0)
    return tokens


def names_are_compatible(seed_name: str, yfinance_name: str) -> bool:
    """True if one name's tokens are a leading subsequence of the other's -- yfinance
    appending real words after the seed's trade name ("BlueScope" / "BlueScope Steel
    Limited") is treated as the SAME company, not a divergence. Still conservative: a
    mismatch anywhere in the shared prefix length fails the check, so "Downer Group" vs
    "Downer EDI Limited" (diverges at the second token) and "Munich Re" vs "Münchener
    Rückversicherungs..." (diverges at the first) are both correctly still flagged --
    neither is a prefix relationship, just two names that happen to start similarly or not
    at all. This is a looser rule than exact-match, which trades a little precision (a
    genuinely wrong company whose name happens to be a prefix of the right one's fuller
    legal name would slip through) for a lot less noise; issue #19's own decision record
    has the reasoning."""
    a = _tokenize_company_name(seed_name)
    b = _tokenize_company_name(yfinance_name)
    if not a or not b:
        return False
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return longer[: len(shorter)] == shorter


def _load_name_overrides() -> dict[tuple[str, str], str]:
    if not NAME_OVERRIDES_PATH.exists():
        return {}
    with open(NAME_OVERRIDES_PATH, encoding="utf-8", newline="") as f:
        return {
            (row["market_code"], row["ticker"]): row["company_name"]
            for row in csv.DictReader(f)
        }


def _load_snapshot() -> dict[tuple[str, str], str]:
    if not NAME_SNAPSHOT_PATH.exists():
        return {}
    with open(NAME_SNAPSHOT_PATH, encoding="utf-8", newline="") as f:
        return {
            (row["market_code"], row["ticker"]): row["yfinance_long_name"]
            for row in csv.DictReader(f)
            if row.get("yfinance_long_name")
        }


def final_seed_names(market_code: str, overrides: dict[tuple[str, str], str]) -> dict[str, str]:
    """ticker -> final (override-applied) company_name for one market, the same name the
    card actually renders (dim_stock.sql coalesces the override over yfinance, and the
    seed's own company_name over the override's absence)."""
    frame = load_constituents(market_code)
    result: dict[str, str] = {}
    for _, row in frame.iterrows():
        ticker = str(row["ticker"])
        result[ticker] = overrides.get((market_code, ticker), row["company_name"])
    return result


def wikipedia_market_codes() -> list[str]:
    configs = load_refresh_configs()
    active = {m.market_code for m in load_markets(active_only=True)}
    return sorted(
        code for code, cfg in configs.items() if code in active and cfg.provider == "wikipedia"
    )


def find_mismatches(
    market_codes: list[str],
    overrides: dict[tuple[str, str], str],
    snapshot: dict[tuple[str, str], str],
) -> tuple[list[str], list[str]]:
    """Returns (mismatches, missing_snapshot_warnings), each a list of formatted lines."""
    mismatches: list[str] = []
    missing: list[str] = []
    for market_code in market_codes:
        try:
            names = final_seed_names(market_code, overrides)
        except FileNotFoundError:
            continue
        for ticker, seed_name in sorted(names.items()):
            snap_name = snapshot.get((market_code, ticker))
            if snap_name is None:
                missing.append(f"{market_code}:{ticker} ({seed_name!r}) -- no snapshot entry")
                continue
            if names_are_compatible(seed_name, snap_name):
                continue
            if (market_code, ticker) in KNOWN_STYLISTIC_DIVERGENCES:
                continue
            mismatches.append(
                f"{market_code}:{ticker} -- seed {seed_name!r} vs yfinance {snap_name!r}"
            )
    return mismatches, missing


def main(argv: list[str] | None = None) -> int:
    market_codes = wikipedia_market_codes()
    overrides = _load_name_overrides()
    snapshot = _load_snapshot()
    mismatches, missing = find_mismatches(market_codes, overrides, snapshot)

    if missing:
        print(f"WARNING: {len(missing)} ticker(s) have no yfinance name snapshot entry:")
        for line in missing:
            print(f"  {line}")
        print(
            "  Run scripts/refresh_yfinance_names.py to refresh the snapshot "
            "(ingestion/constituents/yfinance_name_snapshot.csv)."
        )

    if mismatches:
        print(f"FAILED: {len(mismatches)} seed name(s) do not match yfinance:")
        for line in mismatches:
            print(f"  {line}")
        print(
            "  Fix the seed, or if yfinance is wrong/stylistic, add a row to "
            "dbt_analytics/seeds/company_name_overrides.csv."
        )
        return 1

    print(f"check_company_names_vs_yfinance: {len(market_codes)} market(s) checked, no mismatches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
