"""Tests for the About popover's copy helpers."""

from __future__ import annotations

from datetime import date

from markets import latest_snapshot_label  # noqa: E402
from overflow_menu import MENU_ABOUT_INTRO, MENU_METRICS_LINE, markets_line  # noqa: E402


def test_markets_line_names_only_markets_that_have_cards() -> None:
    """The coverage line is derived, and this is the property that makes deriving worth it.

    A market is onboarded on one branch and first exports cards on the next production run. A
    line built from the registry or from `MARKET_DISPLAY_NAMES` claims coverage in that gap; this
    one cannot, because it only ever names keys of the counts dict.
    """
    line = markets_line({"us_sp500": 400, "de_dax": 39})
    assert line == "Markets: S&P 500, DAX"
    assert "AEX" not in line and "SMI" not in line


def test_markets_line_puts_the_hero_market_first() -> None:
    assert markets_line({"de_dax": 39, "us_sp500": 400}).startswith("Markets: S&P 500")


def test_markets_line_is_empty_without_cards() -> None:
    """Before the first sync `eligible_counts` is {}. Saying nothing beats claiming coverage."""
    assert markets_line({}) == ""


def test_about_intro_does_not_describe_its_own_tone() -> None:
    """Regression guard: an earlier draft said the app "turns filings into a plain-language
    read" -- describing its own tone rather than just being plain, flagged directly by the
    owner ("you don't just say it's plain language, you just be plain"). Pins the phrasing
    this must not regress back to, not the exact wording, which is free to keep changing."""
    assert "plain-language" not in MENU_ABOUT_INTRO.lower()
    assert "plain language" not in MENU_ABOUT_INTRO.lower()


def test_about_intro_mentions_the_ai_read_is_grounded_in_the_cards_own_numbers() -> None:
    assert "AI" in MENU_ABOUT_INTRO
    assert "those same numbers" in MENU_ABOUT_INTRO


def test_menu_metrics_line_has_no_stale_metric_count() -> None:
    """Regression guard: this constant has been rewritten multiple times to drop a stale
    "five" metric-count claim, each time caught only by manual inspection, not a test -- the
    card's per-company-type metric count varies (8/7/4, never exactly 5), so this must never
    assert a specific number again."""
    assert "five" not in MENU_METRICS_LINE.lower()
    assert "—" not in MENU_METRICS_LINE
    assert MENU_METRICS_LINE == "Fundamentals per company, no substitutes"


def test_latest_snapshot_label_picks_max_date() -> None:
    cards = [
        {"is_card_eligible": True, "snapshot_date": "2026-05-01"},
        {"is_card_eligible": True, "snapshot_date": "2026-06-08"},
        {"is_card_eligible": False, "snapshot_date": "2099-01-01"},
    ]
    label = latest_snapshot_label(cards)
    assert label == date(2026, 6, 8).strftime("%B %d, %Y")
