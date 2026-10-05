"""Record real yfinance and Wikipedia payloads for the offline real-shaped fixtures.

Needs the network; run by hand when the recordings should be refreshed, then regenerate the
golden mart with `scripts/check_real_fixture_mart.py --write` and review its diff. Writes
`tests/fixtures/real/`: per market, one JSON per ticker (exactly what `ingest.py` reads from
`yf.Ticker`), the `yf.download` frame for that market's one price batch, and the Wikipedia
page each `provider: wikipedia` market refreshes from. `--ticker MARKET:TICKER` re-records
only the named tickers and keeps every other recording, so the golden diff shows only what
those tickers change.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import requests
import yfinance as yf

from ingestion.constituents.refresh import WIKIPEDIA_USER_AGENT, load_refresh_configs
from ingestion.constituents.seeds import load_constituents
from ingestion.registry import get_market, load_markets
from ingestion.yfinance.ingest import BATCH_SIZE, INFO_FIELDS, LOOKBACK_DAYS
from ingestion.yfinance.symbols import to_yfinance_download_ticker, to_yfinance_ticker

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "real"

# Tickers as `load_constituents` returns them (after ticker_overrides). Per market: ordinary
# companies, a bank or insurer, and the awkward cases this project has actually hit.
FIXTURE_TICKERS: dict[str, list[str]] = {
    "us_sp500": ["AAPL", "KO", "JPM", "BRK-B", "MRNA"],
    "uk_ftse100": ["SHEL", "ULVR", "HSBA", "BT-A.L", "AZN"],
    "jp_nikkei225": ["7203", "6758", "8306", "9984", "4502"],
    "au_asx200": ["BHP", "CSL", "CBA", "XYZ", "FMG"],
    "de_dax": ["SAP", "SIE", "DBK", "ALV", "AIR.PA"],
    "fr_cac40": ["MC.PA", "TTE.PA", "BNP.PA", "MT.AS", "AI.PA"],
    "nl_aex": ["ASML.AS", "INGA.AS", "SHELL.AS", "PHIA.AS", "ADYEN.AS"],
    "ch_smi": ["NESN", "NOVN", "UBSG", "CFR", "ZURN"],
    "es_ibex35": ["SAN.MC", "ITX.MC", "IBE.MC", "MTS.MC", "ROVI.MC"],
    "fi_omxh25": ["NOKIA.HE", "NDA-FI.HE", "KOJAMO.HE", "KESKOB.HE", "KALMAR.HE"],
    "se_omxs30": ["VOLV-B.ST", "ERIC-B.ST", "SEB-A.ST", "ABB.ST", "AZN.ST"],
    "dk_omxc25": ["NOVO-B", "MAERSK-A", "MAERSK-B", "NDA-DK.CO", "DANSKE"],
    "no_obx": ["EQNR", "DNB", "GOGL", "MOWI", "TEL"],
    "ca_tsx60": ["RY", "SHOP", "NA", "CTC-A.TO", "ENB"],
    "it_ftsemib": ["ENEL.MI", "ISP.MI", "RACE.MI", "STLAM.MI", "G.MI"],
}

TICKER_FRAMES = (
    "income_stmt",
    "financials",
    "cashflow",
    "quarterly_income_stmt",
    "quarterly_financials",
    "balance_sheet",
)


def frame_to_json(frame: pd.DataFrame | None) -> dict | None:
    if frame is None:
        return None
    clean = frame.astype(object).where(frame.notna(), None)
    return {
        "index": [str(i) for i in clean.index],
        "columns": [pd.Timestamp(c).isoformat() for c in clean.columns],
        "data": clean.values.tolist(),
        "attrs": dict(frame.attrs),
    }


def fixture_tickers(market_code: str) -> list[str]:
    """The fixture tickers in seed order, which is the order ingestion batches them in."""
    wanted = FIXTURE_TICKERS[market_code]
    seed = load_constituents(market_code)["ticker"].tolist()
    missing = [t for t in wanted if t not in seed]
    if missing:
        raise SystemExit(f"{market_code}: not in the seed (after overrides): {missing}")
    return [t for t in seed if t in wanted]


def _record_ticker(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    payload: dict = {
        "symbol": symbol,
        "info": {key: info[key] for key in sorted(set(INFO_FIELDS.values())) if key in info},
    }
    for name in TICKER_FRAMES:
        payload[name] = frame_to_json(getattr(ticker, name))
    return payload


def _record_prices(batch: list[str]) -> pd.DataFrame:
    downloaded = yf.download(
        batch,
        period=f"{LOOKBACK_DAYS}d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )
    if not isinstance(downloaded.columns, pd.MultiIndex):
        downloaded = pd.concat({batch[0]: downloaded}, axis=1)
    parts = []
    for symbol in downloaded.columns.get_level_values(0).unique():
        part = downloaded[symbol].copy()
        part.columns = [str(c) for c in part.columns]
        part = part.reset_index()
        part.insert(0, "symbol", symbol)
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def record_market(market_code: str) -> dict:
    market = get_market(market_code)
    local = fixture_tickers(market_code)
    if len(local) > BATCH_SIZE:
        raise SystemExit(f"{market_code}: more fixture tickers than one price batch holds")
    out = FIXTURE_DIR / "yfinance" / market_code
    out.mkdir(parents=True, exist_ok=True)

    symbols = {}
    for t in local:
        symbol = to_yfinance_ticker(t, market.exchange_suffix)
        symbols[t] = symbol
        (out / f"{symbol}.json").write_text(
            json.dumps(_record_ticker(symbol), indent=1, default=str) + "\n", encoding="utf-8"
        )
        print(f"  {market_code}: {t} -> {symbol}")

    batch = [to_yfinance_download_ticker(t, market.exchange_suffix) for t in local]
    _record_prices(batch).to_parquet(out / "prices.parquet", index=False)
    return {"tickers": local, "info_symbols": symbols, "download_batch": batch}


def rerecord_tickers(market_code: str, tickers: list[str]) -> dict:
    """Re-record only `tickers` (in their FIXTURE_TICKERS form) in an already-recorded market.

    Every other recording is kept; JSON files for symbols no longer listed are removed. All
    network calls finish before any file is touched, so a failed network call changes nothing.
    """
    market = get_market(market_code)
    local = fixture_tickers(market_code)
    unknown = [t for t in tickers if t not in local]
    if unknown:
        raise SystemExit(f"{market_code}: not in FIXTURE_TICKERS: {unknown}")
    out = FIXTURE_DIR / "yfinance" / market_code
    symbols = {t: to_yfinance_ticker(t, market.exchange_suffix) for t in local}
    batch = [to_yfinance_download_ticker(t, market.exchange_suffix) for t in local]
    redo = {to_yfinance_download_ticker(t, market.exchange_suffix) for t in tickers}
    payloads = {t: _record_ticker(symbols[t]) for t in tickers}
    fresh = _record_prices(sorted(redo))

    kept = pd.read_parquet(out / "prices.parquet")
    kept = kept[kept["symbol"].isin(set(batch) - redo)]
    pd.concat([kept, fresh], ignore_index=True).to_parquet(out / "prices.parquet", index=False)
    for t, payload in payloads.items():
        (out / f"{symbols[t]}.json").write_text(
            json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8"
        )
        print(f"  {market_code}: {t} -> {symbols[t]}")
    for stale in out.glob("*.json"):
        if stale.stem not in symbols.values():
            stale.unlink()
    return {"tickers": local, "info_symbols": symbols, "download_batch": batch}


def record_wikipedia(market_code: str, url: str) -> None:
    response = requests.get(url, headers={"User-Agent": WIKIPEDIA_USER_AGENT}, timeout=30)
    response.raise_for_status()
    out = FIXTURE_DIR / "wikipedia"
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out / f"{market_code}.html.gz", "wt", encoding="utf-8") as handle:
        handle.write(response.text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--market", action="append", dest="markets",
                        help="limit to one or more market_code values (default: every active)")
    parser.add_argument("--ticker", action="append", dest="tickers", metavar="MARKET:TICKER",
                        help="re-record only these tickers, keeping every other recording")
    args = parser.parse_args(argv)
    if args.tickers and args.markets:
        parser.error("--ticker and --market cannot be combined")

    manifest_path = FIXTURE_DIR / "manifest.json"
    if args.tickers:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        by_market: dict[str, list[str]] = {}
        for item in args.tickers:
            code, sep, ticker = item.partition(":")
            if not sep or not ticker:
                parser.error(f"--ticker takes MARKET:TICKER, got {item!r}")
            by_market.setdefault(code, []).append(ticker)
        for code, tickers in by_market.items():
            entry = rerecord_tickers(code, tickers)
            manifest["markets"][code].update(entry)
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        print(f"re-recorded {sum(map(len, by_market.values()))} ticker(s)")
        return 0

    active = [m.market_code for m in load_markets(active_only=True)]
    unlisted = sorted(set(active) - set(FIXTURE_TICKERS))
    if unlisted:
        raise SystemExit(f"active markets with no FIXTURE_TICKERS entry: {unlisted}")
    targets = [c for c in active if not args.markets or c in args.markets]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("markets", {})
    configs = load_refresh_configs()
    for code in targets:
        entry = record_market(code)
        cfg = configs.get(code)
        if cfg and cfg.provider == "wikipedia" and cfg.url:
            record_wikipedia(code, cfg.url)
            entry["wikipedia"] = True
        entry["recorded_at"] = datetime.now(timezone.utc).date().isoformat()
        manifest["markets"][code] = entry
    manifest["markets"] = dict(sorted(manifest["markets"].items()))
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"recorded {len(targets)} market(s) into {FIXTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
