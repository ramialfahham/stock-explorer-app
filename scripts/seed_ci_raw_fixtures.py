"""Write minimal raw parquet fixtures for CI dbt builds (no network)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
SNAPSHOT = date.today()
TICKERS = [f"CI{i:02d}" for i in range(1, 6)]
BANK_TICKER = "CIFIN"
PRE_REVENUE_TICKER = "CIPRE"
ALL_TICKERS = TICKERS + [BANK_TICKER, PRE_REVENUE_TICKER]
TTM_QUARTER_FIXTURE = {
    "qtr_operating_income_0": 25.0,
    "qtr_operating_income_1": 25.0,
    "qtr_operating_income_2": 25.0,
    "qtr_operating_income_3": 25.0,
    "qtr_total_revenue_0": 100.0,
    "qtr_total_revenue_1": 100.0,
    "qtr_total_revenue_2": 100.0,
    "qtr_total_revenue_3": 100.0,
    "qtr_operating_revenue_0": None,
    "qtr_operating_revenue_1": None,
    "qtr_operating_revenue_2": None,
    "qtr_operating_revenue_3": None,
    "qtr_operating_expense_0": None,
    "qtr_operating_expense_1": None,
    "qtr_operating_expense_2": None,
    "qtr_operating_expense_3": None,
    "stmt_operating_income": None,
    "stmt_operating_revenue": None,
    "stmt_operating_expense": None,
}


def _bank_fundamentals(market_code: str) -> dict:
    """One Financial Services fixture per market — bank-shaped so the financial card + eligibility
    are locally verifiable. No current-asset/liability split and no EBITDA (as for real banks);
    has tangible book, ROE, net margin, ROA and a percent dividend yield. The financial required
    pair (statement_roe_pct + net_margin_pct) is present, so it is card-eligible. forward_pe left
    that set with the metric itself; info_forward_pe is still ingested and stored, it
    just no longer gates anything.
    P/TBV = 200/55; net_margin = 12/80*100 = 15%; statement_roe = 11/60*100 ≈ 18.3%; roa = 12/800*100 = 1.5%.
    """
    return {
        "market_code": market_code,
        "ticker": BANK_TICKER,
        "snapshot_date": SNAPSHOT,
        "info_forward_pe": 11.0,
        "info_operating_margins": None,
        "info_revenue_growth": 0.05,
        "info_net_debt": None,
        "info_total_debt": None,
        "info_total_cash": None,
        "info_ebitda": None,
        "info_return_on_equity": 0.18,
        "info_current_ratio": None,
        "info_price_to_book": 1.2,
        "info_price_to_sales": None,
        "info_ev_to_ebitda": None,
        "info_free_cashflow": None,
        "info_market_cap": 200_000_000_000.0,
        "info_sector": "Financial Services",
        "info_currency": "USD",
        "info_long_name": f"CI Fixture {BANK_TICKER} Bank",
        "info_business_summary": (
            f"CI Fixture {BANK_TICKER} is a diversified bank offering retail and commercial banking services."
        ),
        "info_founded_year": 1990,
        "stmt_total_revenue": 80_000_000_000.0,
        "stmt_free_cash_flow": None,
        "stmt_fiscal_period_end": SNAPSHOT,
        "stmt_currency": "USD",
        "stmt_stockholders_equity": 60_000_000_000.0,
        "stmt_total_debt": 100_000_000_000.0,
        "stmt_current_assets": None,
        "stmt_current_liabilities": None,
        "stmt_cash_and_equivalents": 50_000_000_000.0,
        "stmt_tangible_book_value": 55_000_000_000.0,
        "stmt_total_assets": 800_000_000_000.0,
        "stmt_operating_cash_flow": None,
        "stmt_capital_expenditure": None,
        "stmt_interest_expense": None,
        "stmt_net_income": 12_000_000_000.0,
        "stmt_net_income_common": 11_000_000_000.0,
        "info_dividend_yield": 3.5,
        "info_payout_ratio": 0.4,
        **{key: None for key in TTM_QUARTER_FIXTURE},
    }


def _pre_revenue_fundamentals(market_code: str) -> dict:
    """One pre-revenue (loss-making, cash-burning) fixture per market so the survival card +
    eligibility are locally verifiable. Revenue 0 -> pre_revenue; burning cash (negative OCF +
    capex -> computed_fcf < 0); has cash and debt -> net_cash present -> eligible. Market cap is no
    longer required for pre-revenue eligibility (net_cash replaced net_cash_to_market_cap
    and has no price in it). net_cash = 2100-100 = 2000; runway = 2100/700*12 = 36 months;
    burn = 700/12 ≈ 58.3M/mo; working_capital = 2500-400 = 2100M. Fails the operating/bank gates (no ROE, no net margin).
    """
    return {
        "market_code": market_code,
        "ticker": PRE_REVENUE_TICKER,
        "snapshot_date": SNAPSHOT,
        "info_forward_pe": None,
        "info_operating_margins": None,
        "info_revenue_growth": None,
        "info_net_debt": None,
        "info_total_debt": None,
        "info_total_cash": None,
        "info_ebitda": None,
        "info_return_on_equity": None,
        "info_current_ratio": None,
        "info_price_to_book": None,
        "info_price_to_sales": None,
        "info_ev_to_ebitda": None,
        "info_free_cashflow": None,
        "info_market_cap": 5_000_000_000.0,
        "info_sector": "Healthcare",
        "info_currency": "USD",
        "info_long_name": f"CI Fixture {PRE_REVENUE_TICKER} Biotech",
        "info_business_summary": (
            f"CI Fixture {PRE_REVENUE_TICKER} is a clinical-stage biotech developing new therapies; not yet profitable."
        ),
        "info_founded_year": 2015,
        "stmt_total_revenue": 0.0,
        "stmt_free_cash_flow": None,
        "stmt_fiscal_period_end": SNAPSHOT,
        "stmt_currency": "USD",
        "stmt_stockholders_equity": 2_000_000_000.0,
        "stmt_total_debt": 100_000_000.0,
        "stmt_current_assets": 2_500_000_000.0,
        "stmt_current_liabilities": 400_000_000.0,
        "stmt_cash_and_equivalents": 2_100_000_000.0,
        "stmt_tangible_book_value": None,
        "stmt_total_assets": 2_600_000_000.0,
        "stmt_operating_cash_flow": -600_000_000.0,
        "stmt_capital_expenditure": -100_000_000.0,
        "stmt_interest_expense": None,
        "stmt_net_income": -700_000_000.0,
        "stmt_net_income_common": -700_000_000.0,
        "info_dividend_yield": None,
        "info_payout_ratio": None,
        **{key: None for key in TTM_QUARTER_FIXTURE},
    }


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _write_market_fixtures(market_code: str) -> None:
    out = REPO_ROOT / "storage" / "raw" / market_code
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    constituents = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "company_name": f"CI Fixture {ticker}",
                "refreshed_at": now,
                "source": "ci_fixture",
                "ingested_at": now,
            }
            for ticker in ALL_TICKERS
        ]
    )
    constituents.to_parquet(out / "yf_constituents.parquet", index=False)

    prices = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "trading_date": SNAPSHOT,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1_000_000,
                "dividends": 0.0,
                "stock_splits": 0.0,
                "ingested_at": now,
            }
            for ticker in ALL_TICKERS
        ]
    )
    prices.to_parquet(out / "yf_daily_prices.parquet", index=False)

    fundamentals = pd.DataFrame(
        [
            {
                "market_code": market_code,
                "ticker": ticker,
                "snapshot_date": SNAPSHOT,
                "info_forward_pe": 20.0 + i,
                "info_operating_margins": 0.25,
                "info_revenue_growth": 0.08,
                "info_net_debt": 10_000_000_000.0,
                "info_total_debt": None,
                "info_total_cash": None,
                "info_ebitda": 20_000_000_000.0,
                "info_return_on_equity": 0.18,
                "info_current_ratio": 1.5,
                "info_price_to_book": 8.0,
                "info_price_to_sales": 5.0,
                "info_ev_to_ebitda": 15.0,
                "info_free_cashflow": 5_000_000_000.0,
                "info_market_cap": 100_000_000_000.0,
                "info_sector": "Technology",
                "info_currency": "USD",
                "info_long_name": f"CI Fixture {ticker}",
                "info_business_summary": (
                    f"CI Fixture {ticker} designs and sells technology products worldwide."
                ),
                "info_founded_year": 2000 + i,
                "stmt_total_revenue": 50_000_000_000.0,
                "stmt_free_cash_flow": 5_000_000_000.0,
                "stmt_fiscal_period_end": SNAPSHOT,
                "stmt_currency": "USD",
                "stmt_stockholders_equity": 40_000_000_000.0,
                "stmt_total_debt": 15_000_000_000.0,
                "stmt_current_assets": 30_000_000_000.0,
                "stmt_current_liabilities": 20_000_000_000.0,
                "stmt_cash_and_equivalents": 10_000_000_000.0,
                "stmt_tangible_book_value": 35_000_000_000.0,
                "stmt_total_assets": 80_000_000_000.0,
                "stmt_operating_cash_flow": 8_000_000_000.0,
                "stmt_capital_expenditure": -2_000_000_000.0,
                "stmt_interest_expense": 500_000_000.0,
                "stmt_net_income": 6_000_000_000.0,
                "stmt_net_income_common": 6_000_000_000.0,
                # Percent-scale, like the bank fixture below; reverting to a fraction
                # fails assert_percent_scale_passthroughs, not anything naming this line.
                "info_dividend_yield": 2.0,
                "info_payout_ratio": 0.30,
                **TTM_QUARTER_FIXTURE,
            }
            for i, ticker in enumerate(TICKERS, start=1)
        ]
        + [_bank_fundamentals(market_code), _pre_revenue_fundamentals(market_code)]
    )
    fundamentals.to_parquet(out / "yf_fundamentals.parquet", index=False)


def main() -> int:
    markets = _load_active_markets()
    for market_code in markets:
        _write_market_fixtures(market_code)
        print(f"seed_ci_raw_fixtures: wrote fixtures for {market_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
