"""Card copy helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from card_copy import (  # noqa: E402
    BUSINESS_SUMMARY_PREVIEW_WORDS,
    business_summary_is_truncated,
    business_summary_preview,
    metric_analogy,
    metric_gloss,
    metric_label,
    metric_learn_text,
    saved_row_subtitle,
    truncate_words,
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


def test_truncate_words_short_text_unchanged() -> None:
    text = "One two three four five."
    preview, truncated = truncate_words(text, 10)
    assert preview == text
    assert truncated is False


def test_truncate_words_adds_ellipsis() -> None:
    text = " ".join(f"word{i}" for i in range(25))
    preview, truncated = truncate_words(text, 20)
    assert truncated is True
    assert preview.endswith("…")
    assert len(preview.split()) == 20


def test_business_summary_preview_uses_original_wording() -> None:
    card = {
        "business_summary": (
            "NVIDIA Corporation provides graphics and compute products for gaming "
            "and professional markets and is a leader in accelerated computing "
            "and artificial intelligence."
        ),
    }
    preview = business_summary_preview(card, max_words=12)
    assert preview is not None
    assert preview.startswith("NVIDIA Corporation provides graphics")
    assert preview.endswith("…")


def test_business_summary_preview_empty_when_no_summary() -> None:
    assert business_summary_preview({}) is None
    assert business_summary_preview({"business_summary": "   "}) is None


def test_business_summary_is_truncated() -> None:
    long_card = {
        "business_summary": " ".join(f"word{i}" for i in range(30)),
    }
    short_card = {"business_summary": "Short company blurb."}
    assert business_summary_is_truncated(long_card) is True
    assert business_summary_is_truncated(short_card) is False
    assert BUSINESS_SUMMARY_PREVIEW_WORDS == 20
