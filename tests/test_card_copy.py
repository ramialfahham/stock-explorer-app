"""Card copy helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from card_copy import (  # noqa: E402
    company_plain_summary_line,
    company_summary_has_full_description,
    first_sentence,
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


def test_first_sentence_stops_at_period() -> None:
    abnb = (
        "Airbnb, Inc., together with its subsidiaries, operates a platform "
        "for stays and experiences. It connects hosts and guests worldwide."
    )
    assert first_sentence(abnb).startswith("Airbnb, Inc.")
    assert first_sentence(abnb).endswith(".")


def test_company_plain_summary_line_with_founded_year() -> None:
    card = {
        "business_summary": (
            "NVIDIA Corporation provides graphics and compute products. "
            "It serves gaming, data center, and automotive markets."
        ),
        "company_founded_year": 1993,
    }
    line = company_plain_summary_line(card)
    assert line is not None
    assert line.startswith("Founded 1993 · NVIDIA Corporation")


def test_company_plain_summary_line_without_founded_year() -> None:
    card = {
        "business_summary": (
            "NVIDIA Corporation provides graphics and compute products. "
            "It serves gaming, data center, and automotive markets."
        ),
    }
    line = company_plain_summary_line(card)
    assert line is not None
    assert not line.startswith("Founded")
    assert line.startswith("NVIDIA Corporation")


def test_company_plain_summary_line_empty_when_no_summary() -> None:
    assert company_plain_summary_line({}) is None
    assert company_plain_summary_line({"business_summary": "   "}) is None


def test_company_summary_has_full_description() -> None:
    long_card = {
        "business_summary": (
            "Airbnb, Inc. operates a platform for stays. "
            "Additional detail about markets and history follows here."
        ),
    }
    short_card = {"business_summary": "One sentence only."}
    assert company_summary_has_full_description(long_card) is True
    assert company_summary_has_full_description(short_card) is False
