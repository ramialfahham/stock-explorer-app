"""Card copy helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from card_copy import (  # noqa: E402
    metric_analogy,
    metric_gloss,
    metric_label,
    metric_learn_text,
    saved_row_subtitle,
)


def test_metric_gloss_net_cash_when_ratio_negative() -> None:
    assert metric_gloss("net_debt_to_ebitda", -3.6) == "Net cash — cash on hand exceeds debt"


def test_metric_gloss_leverage_when_ratio_positive() -> None:
    gloss = metric_gloss("net_debt_to_ebitda", 2.5)
    assert "repay" in gloss.lower() or "debt" in gloss.lower()


def test_metric_learn_net_cash_mentions_sign() -> None:
    text = metric_learn_text("net_debt_to_ebitda", -1.0)
    assert "net cash" in text.lower()


def test_metric_analogy_net_cash() -> None:
    text = metric_analogy("net_debt_to_ebitda", -0.5)
    assert "cash" in text.lower()


def test_saved_row_subtitle_ticker_and_sector() -> None:
    card = {"ticker": "AAPL", "sector": "Technology"}
    assert saved_row_subtitle(card) == "AAPL · Technology"


def test_metric_label_annual_operating_margin() -> None:
    card = {"ebit_margin_basis": "annual_latest"}
    assert metric_label("ebit_margin_pct", card) == "Operating margin (annual)"
