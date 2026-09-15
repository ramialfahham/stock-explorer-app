"""End-to-end AppTest coverage for frontend/app.py's three bottom-nav tabs.

Drives the real script via streamlit.testing.v1.AppTest -- a full-script check, distinct from
test_app.py's direct-import unit tests of app.py's pure helpers. This targets the cross-tab
session_state flow (save a card, remove a saved card, search by ticker) that pure-function
tests structurally cannot reach, since they never instantiate a real script or session.

Three real I/O boundaries are stubbed at their module attribute (frontend/supabase_client.py,
frontend/supabase_cards.py, frontend/saved_news.py); the saved-list cookie is faked at
browser_storage._request_cookies, since AppTest carries no request headers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Button

import browser_storage
import saved_news
import supabase_cards
import supabase_client

APP_PATH = Path(__file__).resolve().parents[2] / "frontend" / "app.py"

FIXTURE_CARDS: list[dict[str, Any]] = [
    {
        "market_code": "us_sp500",
        "ticker": "ALFA",
        "company_name": "Alpha Testing Corp",
        "sector": "Technology",
        "is_card_eligible": True,
        "business_summary": "Alpha Testing Corp is a synthetic fixture used for AppTest coverage.",
        "snapshot_date": "2026-08-01",
        "currency": "USD",
    },
    {
        "market_code": "us_sp500",
        "ticker": "BETA",
        "company_name": "Beta Sample Inc",
        "sector": "Healthcare",
        "is_card_eligible": True,
        "business_summary": "Beta Sample Inc is a synthetic fixture used for AppTest coverage.",
        "snapshot_date": "2026-08-01",
        "currency": "USD",
    },
]


def _fixture_cards() -> list[dict[str, Any]]:
    return [dict(card) for card in FIXTURE_CARDS]


def _assert_clean(at: AppTest) -> None:
    """app.py's _load_cards() catches a Supabase fetch failure into st.error() rather than
    raising -- a broken mock shows up as a quiet empty list, not a Python traceback. Assert
    this after every .run(), not just that .run() didn't raise, so a mocking mistake points at
    itself instead of surfacing as a confusing downstream "button not found"."""
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def _row_button(at: AppTest, key: str) -> Button | None:
    try:
        return at.button(key=key)
    except KeyError:
        return None


def _save_interaction(ticker: str, *, seconds: int) -> dict[str, Any]:
    """Matches browser_storage.append_interaction's row shape exactly (market_code/ticker/
    action/created_at) so it's indistinguishable from a real save once seeded. `seconds`
    only needs to make created_at ordering distinct between rows; the actual value is never
    asserted on."""
    return {
        "market_code": "us_sp500",
        "ticker": ticker,
        "action": "save",
        "created_at": datetime(2026, 8, 1, tzinfo=timezone.utc)
        .replace(second=seconds)
        .isoformat(),
    }


@pytest.fixture
def app_test(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("SUPABASE_URL", "https://fixture.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "fixture-anon-key")
    # The deck and the card face are two separate fetches now, so both need mocking: the deck
    # feeds the Discover/Saved/Search lists, fetch_card_detail feeds whichever card is opened.
    monkeypatch.setattr(supabase_cards, "fetch_deck", lambda client: _fixture_cards())
    monkeypatch.setattr(
        supabase_cards,
        "fetch_card_detail",
        lambda client, market_code, ticker: next(
            (
                c
                for c in _fixture_cards()
                if c["market_code"] == market_code and c["ticker"] == ticker
            ),
            None,
        ),
    )
    monkeypatch.setattr(supabase_cards, "export_lacks_business_summary", lambda client: False)
    # app.py caches the deck with @st.cache_data keyed only on an unhashed client, so the key is
    # constant and one test's deck would otherwise be served to the next.
    st.cache_data.clear()
    monkeypatch.setattr(supabase_client, "get_anon_client", lambda: object())
    monkeypatch.setattr(saved_news, "_fetch_news", lambda symbol: [])
    monkeypatch.setattr(browser_storage, "_request_cookies", lambda: {})
    return AppTest.from_file(str(APP_PATH), default_timeout=15)


@pytest.fixture
def cookie_scripts(monkeypatch) -> list[str]:
    """Every body app.py hands to components.html: the cookie write and the one-time
    localStorage migration. AppTest never executes them; the test reads them."""
    out: list[str] = []
    monkeypatch.setattr(browser_storage.components, "html", lambda body, height=0: out.append(body))
    return out


def test_discover_pool_shows_fixture_cards(app_test: AppTest) -> None:
    at = app_test.run()
    _assert_clean(at)
    for card in FIXTURE_CARDS:
        key = f"discover_row_{card['market_code']}::{card['ticker']}"
        assert _row_button(at, key) is not None


def test_save_card_from_discover_appears_in_saved(app_test: AppTest, cookie_scripts) -> None:
    at = app_test.run()
    at = at.button(key="discover_row_us_sp500::ALFA").click().run()
    _assert_clean(at)
    writes_before = [b for b in cookie_scripts if "ss_saved_" in b and "localStorage" not in b]
    assert writes_before == []
    at = at.button(key="discover_save").click().run()
    _assert_clean(at)
    # The save ends its run with st.rerun(); the write is flushed by the run that follows,
    # through main()'s flush_storage_writes(). Remove that call and this is the assertion
    # that fails.
    writes = [b for b in cookie_scripts if "ss_saved_" in b and "localStorage" not in b]
    assert len(writes) == 1
    assert "us_sp500:ALFA:" in writes[0]

    at = at.segmented_control(key="bottom_nav").set_value("Saved").run()
    _assert_clean(at)
    assert _row_button(at, "saved_row_us_sp500::ALFA") is not None


def test_remove_from_saved_only_removes_that_card(app_test: AppTest) -> None:
    """Regression-shaped by construction: two cards are saved so removal is proven to be
    scoped to the selected one, not a blanket clear that happens to look right with only one
    saved item.

    Both "save" interactions are seeded directly onto session_state rather than driven by
    clicking Discover's Save button on each card in turn. This is deliberate, not a shortcut:
    focusing two DIFFERENT cards' full detail views in the same AppTest session (each renders
    metric_school.py's "Understand these numbers" playground widgets, whose keys are ticker-
    scoped -- frontend/metric_school.py's _key()) swaps the full set of active widget keys and
    triggers a KeyError on the next .run(), from Streamlit's own widget-cleanup path
    (streamlit/runtime/state/session_state.py's _compact_state, called by
    SessionState.on_script_will_rerun, itself invoked inside ScriptRunner._run_script --
    a method AppTest's LocalScriptRunner does not override, so it runs unmodified there too).

    That underlying condition is real, shared production code, not an AppTest artifact --
    Streamlit's own session_state.py wraps this exact cleanup path in `except KeyError: pass`,
    citing a known upstream issue (streamlit/issues/7206) about stale widget metadata. A single
    manual pass against a real dev server (real Supabase data, real browser: opened one card,
    saved it, opened a different card, saved it, no crash, no server-log traceback) did NOT
    reproduce a user-visible failure -- but that's consistent with, not proof against, the
    mechanism being real: production's own defensive except-KeyError would silently swallow it
    there, while AppTest's get_widget_states() (element_tree.py) reads widget state without the
    same protection, turning a condition production tolerates into a hard test failure. One
    unrepeated manual pass does not rule out a rarer or timing-sensitive path still causing a
    real problem; this is flagged to the owner as an open question, not asserted as closed.

    Seeding here is still the right fix for THIS test either way -- it sidesteps an AppTest-
    harness gap (missing production's own defensive handling) while keeping the actual thing
    under test -- does "Remove from saved" scope to just the selected card -- driven through
    the real Saved-tab UI, unstubbed. Fixing metric_school.py's key scheme or Streamlit's own
    upstream behavior is out of scope here regardless of how the open question resolves."""
    at = app_test.run()
    at.session_state["interactions"] = [
        _save_interaction("ALFA", seconds=1),
        _save_interaction("BETA", seconds=2),
    ]
    at.session_state["_interactions_storage_loaded"] = True
    at = at.run()
    _assert_clean(at)

    at = at.segmented_control(key="bottom_nav").set_value("Saved").run()
    assert _row_button(at, "saved_row_us_sp500::ALFA") is not None
    assert _row_button(at, "saved_row_us_sp500::BETA") is not None

    at = at.button(key="saved_row_us_sp500::ALFA").click().run()
    _assert_clean(at)  # exercises the saved-news yfinance stub too
    at = at.button(key="saved_remove_current").click().run()
    _assert_clean(at)

    assert _row_button(at, "saved_row_us_sp500::ALFA") is None
    assert _row_button(at, "saved_row_us_sp500::BETA") is not None


def test_search_by_ticker_finds_card(app_test: AppTest) -> None:
    at = app_test.run()
    at = at.segmented_control(key="bottom_nav").set_value("Search").run()
    # The search box is the only st.text_input in the app, and deliberately unkeyed (see
    # app.py's own docstring) -- addressed by index rather than key.
    at = at.text_input[0].set_value("ALFA").run()
    _assert_clean(at)
    assert _row_button(at, "search_us_sp500_ALFA") is not None
    assert _row_button(at, "search_us_sp500_BETA") is None


def test_search_with_no_match_shows_warning(app_test: AppTest) -> None:
    at = app_test.run()
    at = at.segmented_control(key="bottom_nav").set_value("Search").run()
    at = at.text_input[0].set_value("nonexistent-zzz").run()
    _assert_clean(at)
    assert len(at.warning) == 1
    assert "nonexistent-zzz" in at.warning[0].value


def _rendered_markdown(at: AppTest) -> list[str]:
    """Every st.markdown value except the injected stylesheet, whose CSS mentions every
    class name and would match any selector-shaped probe."""
    return [m.value for m in at.markdown if not m.value.lstrip().startswith("<style>")]


def _header_is_compact(at: AppTest) -> bool:
    return any("ss-brand-header--compact" in v for v in _rendered_markdown(at))


def _scope_stats_line_present(at: AppTest) -> bool:
    return any("ss-header-stats--solo" in v for v in _rendered_markdown(at))


def test_header_compacts_while_a_card_is_open_and_restores_on_back(app_test: AppTest) -> None:
    """The call site, not the helper: _discovery_page must read the focus key before the nav
    widget renders and choose the compact header, then choose the full one again on Back."""
    at = app_test.run()
    _assert_clean(at)
    assert not _header_is_compact(at)
    assert _scope_stats_line_present(at)

    at = at.button(key="discover_row_us_sp500::ALFA").click().run()
    _assert_clean(at)
    assert _header_is_compact(at)
    assert not _scope_stats_line_present(at), "the stats line is gone while a card is open"
    assert not any("ss-header-stats--inline" in v for v in _rendered_markdown(at)), (
        "Discover's back row shows no saved count -- Saved-tab only"
    )

    at = at.button(key="discover_back_to_list").click().run()
    _assert_clean(at)
    assert not _header_is_compact(at)
    assert _scope_stats_line_present(at)


def test_saved_count_shows_only_on_the_saved_tab(app_test: AppTest, cookie_scripts) -> None:
    """The "N saved" chrome is Saved-tab-only: it does not render on Discover's list header,
    Discover's back row, or Search."""
    at = app_test.run()
    at = at.button(key="discover_row_us_sp500::ALFA").click().run()
    at = at.button(key="discover_save").click().run()
    _assert_clean(at)

    at = at.segmented_control(key="bottom_nav").set_value("Discover").run()
    _assert_clean(at)
    assert not any("saved" in v for v in _rendered_markdown(at)), (
        "Discover's list header must not mention the saved count"
    )

    at = at.segmented_control(key="bottom_nav").set_value("Search").run()
    _assert_clean(at)
    assert not any("saved" in v for v in _rendered_markdown(at)), (
        "Search must not render a saved count at all, even before a query is typed"
    )

    at = at.segmented_control(key="bottom_nav").set_value("Saved").run()
    _assert_clean(at)
    assert any("1 saved" in v and "ss-header-stats--solo" in v for v in _rendered_markdown(at))

    at = at.button(key="saved_row_us_sp500::ALFA").click().run()
    _assert_clean(at)
    assert any("1 saved" in v and "ss-header-stats--inline" in v for v in _rendered_markdown(at)), (
        "Saved's own back row keeps the saved count"
    )


def test_switching_to_saved_while_a_discover_card_is_open_restores_the_header(
    app_test: AppTest,
) -> None:
    at = app_test.run()
    at = at.button(key="discover_row_us_sp500::ALFA").click().run()
    assert _header_is_compact(at)
    at = at.segmented_control(key="bottom_nav").set_value("Saved").run()
    _assert_clean(at)
    assert not _header_is_compact(at)
