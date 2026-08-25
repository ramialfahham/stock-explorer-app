"""Regression guard for a recurring CSS bug class in frontend/styles.py.

WHY THIS FILE EXISTS: a marker `<div>` rendered via its own `st.markdown()` call,
immediately followed by a Streamlit layout primitive (`st.columns()`,
`st.container(horizontal=True)`), styled via `.marker + div[data-testid="..."]`
-- looks reasonable, and is wrong: Streamlit wraps the marker in its own
`stElementContainer`, so the marker's own next sibling is nothing; the real
sibling relationship is one level up, between that `stElementContainer` and the
following `stLayoutWrapper`. This exact bug recurred five times across two
separate PRs (`.ss-card-footer-shell`'s own separator rule, `.ss-freshness`, the
Yahoo Finance link button, `.ss-action-shell`, `.ss-nav-row-marker`) before
anything caught it -- every prior fix was found only by live, one-off browser
inspection, never by a test (`frontend/styles.py` had zero test coverage before
this file). This can't run a browser, so it can't verify a selector actually
MATCHES something live -- but it CAN verify the specific broken SHAPE never
reappears, which is the shape every one of those five bugs shared.

Verified this test fails against the broken form: temporarily reverted one fixed
rule back to `.ss-nav-row-marker + div[data-testid="stHorizontalBlock"]` and
confirmed test_no_marker_uses_the_broken_sibling_shape failed with the expected
message, before keeping it.
"""

from __future__ import annotations

import pathlib
import re

# tests/frontend/test_styles.py -> parents[0]=frontend, [1]=tests, [2]=repo root.
STYLES_FILE = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "styles.py"

# A `.ss-*` marker class directly followed by a plain `+ div[data-testid=...]` sibling
# combinator -- the exact shape of every dead-selector instance found so far. The correct
# form wraps the marker in `[data-testid="stElementContainer"]:has(.marker) + ...` instead,
# which does not contain this substring (the marker sits inside `:has(...)`, immediately
# followed by `)`, never by a bare `+`).
BROKEN_SIBLING_PATTERN = re.compile(r'\.ss-[\w-]+\s*\+\s*div\[data-testid=')

# The corrected shape, as it actually appears in frontend/styles.py today.
CORRECT_SIBLING_PATTERN = re.compile(
    r'\[data-testid="stElementContainer"\]:has\(\.ss-[\w-]+\)\s*\+\s*\[data-testid="stLayoutWrapper"\]'
)

# Floor, not an exact count -- a future refactor that changes how many rules use this
# pattern shouldn't break this test for no reason. Today: .ss-card-footer-shell (x3),
# .ss-action-shell (x1), .ss-nav-row-marker (x11), .ss-icon-btn-marker (x1) = 16.
MIN_CORRECT_INSTANCES = 5


def test_no_marker_uses_the_broken_sibling_shape():
    css = STYLES_FILE.read_text(encoding="utf-8")
    matches = BROKEN_SIBLING_PATTERN.findall(css)
    assert not matches, (
        f"found {len(matches)} CSS rule(s) using the broken `.marker + div[data-testid=...]` "
        f"shape: {matches!r}. A marker <div>'s own next sibling is nothing -- Streamlit "
        f"wraps it in its own stElementContainer first, one level up. Use "
        f'`[data-testid="stElementContainer"]:has(.marker) + [data-testid="stLayoutWrapper"]` '
        f"instead (see frontend/styles.py's own comments near .ss-card-footer-shell for the "
        f"full explanation)."
    )


def test_the_correct_sibling_shape_is_actually_present():
    """Vacuity guard for the test above: if this ever drops to zero, the negative
    assertion would pass trivially because there's nothing left to check, not
    because the bug is actually fixed everywhere."""
    css = STYLES_FILE.read_text(encoding="utf-8")
    matches = CORRECT_SIBLING_PATTERN.findall(css)
    assert len(matches) >= MIN_CORRECT_INSTANCES, (
        f"only {len(matches)} correctly-scoped marker-sibling rule(s) found (want >= "
        f"{MIN_CORRECT_INSTANCES}) -- either a real fix regressed back to the broken shape, "
        f"or this pattern has drifted from what frontend/styles.py actually uses now."
    )
