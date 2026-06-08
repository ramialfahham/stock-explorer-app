"""Shared card metric formulas — mirror dbt int_stock__card_metrics.sql."""

from __future__ import annotations

from typing import Any

from ingestion.yfinance.quarterly import TTM_QUARTERS

QTR_OPERATING_INCOME_KEYS = tuple(f"qtr_operating_income_{i}" for i in range(TTM_QUARTERS))
QTR_TOTAL_REVENUE_KEYS = tuple(f"qtr_total_revenue_{i}" for i in range(TTM_QUARTERS))


def effective_net_debt(row: dict[str, Any]) -> float | None:
    net_debt = row.get("info_net_debt")
    if net_debt is not None:
        return float(net_debt)
    total_debt = row.get("info_total_debt")
    total_cash = row.get("info_total_cash")
    if total_debt is not None and total_cash is not None:
        return float(total_debt) - float(total_cash)
    return None


def operating_margin_ttm_pct(row: dict[str, Any]) -> float | None:
    """TTM operating margin from four quarterly statement values (mirrors dbt)."""
    op_values = [row.get(key) for key in QTR_OPERATING_INCOME_KEYS]
    rev_values = [row.get(key) for key in QTR_TOTAL_REVENUE_KEYS]
    if any(value is None for value in op_values + rev_values):
        return None
    op_sum = sum(float(value) for value in op_values)  # type: ignore[arg-type]
    rev_sum = sum(float(value) for value in rev_values)  # type: ignore[arg-type]
    if rev_sum == 0:
        return None
    return op_sum / rev_sum * 100.0


def compute_card_metrics_from_raw(row: dict[str, Any]) -> dict[str, float | None]:
    """Compute the five card metrics from landed yfinance raw fields."""
    forward_pe = row.get("info_forward_pe")
    ebit_margin_pct = row.get("info_operating_margins")
    revenue_growth_yoy_pct = row.get("info_revenue_growth")
    net_debt = effective_net_debt(row)
    ebitda = row.get("info_ebitda")
    fcf = row.get("stmt_free_cash_flow")
    revenue = row.get("stmt_total_revenue")

    net_debt_to_ebitda = None
    if net_debt is not None and ebitda is not None and float(ebitda) != 0:
        net_debt_to_ebitda = net_debt / float(ebitda)

    fcf_margin_pct = None
    if fcf is not None and revenue is not None and float(revenue) != 0:
        fcf_margin_pct = float(fcf) / float(revenue) * 100.0

    return {
        "forward_pe": float(forward_pe) if forward_pe is not None else None,
        "ebit_margin_pct": float(ebit_margin_pct) * 100.0 if ebit_margin_pct is not None else None,
        "revenue_growth_yoy_pct": float(revenue_growth_yoy_pct) * 100.0
        if revenue_growth_yoy_pct is not None
        else None,
        "net_debt_to_ebitda": net_debt_to_ebitda,
        "fcf_margin_pct": fcf_margin_pct,
    }


def reference_operating_margin_info(info: dict[str, Any]) -> float | None:
    """Yahoo info operatingMargins × 100 — often latest quarter, not TTM."""
    raw = info.get("operatingMargins")
    if raw is None:
        return None
    return float(raw) * 100.0


def reference_operating_margin_ttm(row: dict[str, Any]) -> float | None:
    """TTM operating margin from landed quarterly fields or live ticker object."""
    ttm = operating_margin_ttm_pct(row)
    if ttm is not None:
        return ttm
    ticker = row.get("_yf_ticker")
    if ticker is not None:
        from ingestion.yfinance.quarterly import land_quarterly_ttm_fields

        return operating_margin_ttm_pct(land_quarterly_ttm_fields(ticker))
    return None


def reference_fcf_margin_from_info(info: dict[str, Any]) -> float | None:
    """Yahoo-comparable trailing-style FCF margin when info fields exist."""
    fcf = info.get("freeCashflow")
    revenue = info.get("totalRevenue")
    if fcf is None or revenue is None or float(revenue) == 0:
        return None
    return float(fcf) / float(revenue) * 100.0


def pct_drift(mart: float | None, live: float | None) -> float | None:
    if mart is None or live is None:
        return None
    if live == 0:
        return None
    return abs(mart - live) / abs(live) * 100.0
