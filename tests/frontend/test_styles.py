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


# The OTHER recurring bug class in this file, distinct from the sibling-combinator one
# above: a bare single-class `<p>` selector (`.ss-thing { font-size: ... }`) silently
# loses font-size and any non-zero margin to a Streamlit emotion-cache `<ancestor> p`
# reset at higher specificity. MR #29 fixed ~24 of these at once. Every such rule must
# be scoped under an ancestor class (or use !important where no ancestor exists), which
# is what these labels do via `.ss-card-identity .ss-block-label`.
CARD_FACE_P_CLASSES = ("ss-block-label",)


def test_card_face_p_class_rules_are_scoped_not_bare():
    """A bare `.ss-block-label { font-size: ... }` would render at Streamlit's paragraph
    size instead of ours, and look correct in the source while being wrong on screen --
    the exact failure mode MR #29 had to fix across two dozen classes.

    Verified to fail against the broken form: temporarily rewrote
    `.ss-card-identity .ss-block-label` back to a bare `.ss-block-label` and confirmed
    this test failed before keeping it, same check the sibling guard above documents."""
    css = STYLES_FILE.read_text(encoding="utf-8")
    for cls in CARD_FACE_P_CLASSES:
        bare = re.compile(r"(?m)^\s*\.%s\s*(,|\{)" % re.escape(cls))
        assert not bare.search(css), (
            f"`.{cls}` is used as a bare single-class selector at the start of a rule. "
            f"A Streamlit emotion-cache `<ancestor> p` reset outranks it, so the declared "
            f"font-size and margins are silently dropped on screen. Scope it under its "
            f"wrapper (e.g. `.ss-card-identity .{cls}`) instead."
        )
        scoped = re.compile(r"\.ss-[\w-]+\s+\.%s\s*(,|\{)" % re.escape(cls))
        assert scoped.search(css), (
            f"no scoped rule found for `.{cls}` -- expected something like "
            f"`.ss-card-identity .{cls}`. If the class was renamed or removed, update "
            f"CARD_FACE_P_CLASSES so this guard keeps testing something real."
        )


# A THIRD recurring bug class in this file, distinct from the two above: the invisible
# full-row tap-target button (`.ss-row`'s `[data-testid="stButton"]`, `position: absolute;
# inset: 0`) is meant to fill the row's own `stVerticalBlock` container. But Streamlit sets
# `position: relative` on every `stElementContainer`, including the one that wraps the button
# directly -- and since that wrapper is nearer than the intended `stVerticalBlock`, it becomes
# the button's containing block instead. That wrapper has no content of its own (its only
# child is absolutely positioned), so it collapses to zero height, and the button renders at
# its `min-height` starting wherever that zero-height box falls in normal flow: right after
# the row's own markdown, not on top of it.
TAP_TARGET_NEUTRALIZER_PATTERN = re.compile(
    r':has\(\.ss-row-group\)\s+div\[data-testid="stVerticalBlock"\]:has\(>\s*'
    r'\[data-testid="stElementContainer"\]\s+\.ss-row\)\s+'
    r'\[data-testid="stElementContainer"\]:has\(>\s*\[data-testid="stButton"\]\)\s*\{'
    r'[^}]*position:\s*static\s*!important'
)


def test_row_tap_target_neutralizes_its_own_element_container_position():
    """Confirmed live before this test existed: every row's tap target rendered entirely
    below its own visible row, overlapping the next row's top edge, so clicking a row opened
    the one above it, and the first row (nothing above it to catch the click) did nothing at
    all -- this broke the core interaction of Discover, Saved, and Search alike, since all
    three share this row primitive. Confirmed fixed the same way: after adding the rule this
    test guards, every sampled row's tap-target bounding box matched its own visible row
    exactly, including real pixel hit-testing (`document.elementFromPoint`) at both the top
    and bottom edge of several rows.

    This can't run a browser, so it can't verify the fix actually renders correctly live --
    but it can verify the neutralizing rule's shape never regresses out of frontend/styles.py.
    """
    css = STYLES_FILE.read_text(encoding="utf-8")
    assert TAP_TARGET_NEUTRALIZER_PATTERN.search(css), (
        "no rule found resetting `position` on the stElementContainer that directly wraps "
        "a row's tap-target button. Without it, that wrapper's own Streamlit-default "
        "`position: relative` outranks the intended `stVerticalBlock` anchor (it's nearer), "
        "the wrapper collapses to zero height since its only child is absolutely positioned, "
        "and the button renders below its own row instead of on top of it -- the exact bug "
        "this test exists to catch, confirmed live via document.elementFromPoint hit-testing "
        "before the fix and after."
    )


# A FOURTH recurring bug class in this file, distinct from the three above, but caused by
# the same row-primitive rule block: `:has()` matches at ANY descendant depth, not just the
# nearest one, so a bare `:has(.ss-row)` on `div[data-testid="stVerticalBlock"]` matches not
# only each row's own small per-row container, but also the single big stVerticalBlock that
# wraps the *entire* list (every row is nested inside it, so it too "has a .ss-row somewhere
# below it"). Confirmed live while adding Discover's pagination controls: a later,
# unrelated st.button() rendered after the row loop, inside that same big wrapper, silently
# inherited the row-tap-target's `position: absolute; inset: 0` -- meant only for each row's
# own button -- and stretched to the full list's height (~2780px) instead of a normal button.
BARE_HAS_ROW_PATTERN = re.compile(r'stVerticalBlock"\]:has\(\.ss-row\)')


def test_no_row_rule_uses_the_bare_has_row_shape():
    css = STYLES_FILE.read_text(encoding="utf-8")
    matches = BARE_HAS_ROW_PATTERN.findall(css)
    assert not matches, (
        f"found {len(matches)} CSS rule(s) using the bare "
        f'`div[data-testid="stVerticalBlock"]:has(.ss-row)` shape: {matches!r}. `:has()` '
        f"matches at any descendant depth, so this also matches the single big stVerticalBlock "
        f"wrapping the entire row list, not just each row's own small container -- any later "
        f"st.button() sharing that same big wrapper (e.g. Discover's pagination controls) "
        f'silently inherits these row-only rules. Use `:has(> [data-testid="stElementContainer"] '
        f".ss-row)` instead (direct child), which only matches each row's own container."
    )


def test_the_direct_child_row_shape_is_actually_present():
    """Vacuity guard for the test above, matching this file's own established pattern: if this
    ever drops to zero, the negative assertion above would pass trivially because there's
    nothing left to check, not because the bug is actually fixed everywhere."""
    css = STYLES_FILE.read_text(encoding="utf-8")
    pattern = re.compile(
        r'stVerticalBlock"\]:has\(>\s*\[data-testid="stElementContainer"\]\s+\.ss-row\)'
    )
    matches = pattern.findall(css)
    assert len(matches) >= 5, (
        f"only {len(matches)} correctly-scoped direct-child row-container rule(s) found (want "
        f">= 5) -- either a real fix regressed back to the bare `:has(.ss-row)` shape, or this "
        f"pattern has drifted from what frontend/styles.py actually uses now."
    )


# --- Type scale ---------------------------------------------------------------------------
# Owner-set mobile scale: body 14px, captions 13px, chips and small labels 12px and nothing
# below. Two sizes stay literal on purpose: the brand wordmark and the icon-button glyph,
# neither of which is reading text.

FONT_SIZE_DECL = re.compile(r"\bfont-size\s*:\s*([^;]+);")
# The `font:` shorthand sets a size without the word "font-size", so it is refused outright.
FONT_SHORTHAND = re.compile(r"\bfont\s*:")
TOKEN_DECL = re.compile(r"--ss-([\w-]+)\s*:\s*([\d.]+)(rem|px|em|%)\s*;")
LITERAL_SIZES_ALLOWED = {"1.35rem", "1.05rem !important"}
SMALLEST_TEXT_TOKEN_REM = 0.75
SIZE_TOKENS = {"value", "title", "body", "label", "caption-size", "row-title"}


def _stylesheet() -> str:
    return STYLES_FILE.read_text(encoding="utf-8")


def test_every_font_size_is_a_size_token_or_a_named_exception():
    """A spacing or radius token, or a new token outside SIZE_TOKENS, would pass a bare
    var(--ss-*) check and never meet the floor test; the name must be one of the six."""
    offenders = []
    for value in FONT_SIZE_DECL.findall(_stylesheet()):
        if value in LITERAL_SIZES_ALLOWED:
            continue
        token = re.fullmatch(r"var\(--ss-([\w-]+)\)( !important)?", value)
        if token is None or token.group(1) not in SIZE_TOKENS:
            offenders.append(value)
    assert offenders == [], f"font-size(s) not on a size token: {offenders}"
    assert not FONT_SHORTHAND.search(_stylesheet()), "font: shorthand bypasses the size tokens"


def test_no_text_size_token_falls_below_the_floor():
    found = {name: (float(n), unit) for name, n, unit in TOKEN_DECL.findall(_stylesheet())}
    missing = SIZE_TOKENS - set(found)
    assert missing == set(), f"missing size tokens: {missing}"
    not_rem = {n: u for n, (_, u) in found.items() if n in SIZE_TOKENS and u != "rem"}
    assert not_rem == {}, f"size token(s) not in rem: {not_rem}"
    sizes = {n: v for n, (v, _) in found.items() if n in SIZE_TOKENS}
    too_small = {n: v for n, v in sizes.items() if v < SMALLEST_TEXT_TOKEN_REM}
    assert too_small == {}, f"size token(s) under {SMALLEST_TEXT_TOKEN_REM}rem: {too_small}"


def test_body_copy_uses_the_body_token_not_the_caption_token():
    """The whole point of the scale: body copy was borrowing the caption size."""
    sheet = _stylesheet()
    for selector in (
        ".ss-health-block .ss-ai-read-list li",
        ".ss-card-identity .ss-company-summary",
        ".ss-metric .ss-metric-gloss",
        ".ss-metric-learn-item .ss-metric-learn-body",
    ):
        assert selector + " {" in sheet, f"{selector} rule is missing"
        block = sheet.split(selector + " {", 1)[1].split("}", 1)[0]
        assert "font-size: var(--ss-body)" in block, f"{selector} is not on the body token"


def test_financial_caveat_is_styled_where_it_renders():
    """The caveat moved out of the health block into the metrics section (issue #11). A rule
    still scoped under .ss-health-block would match nothing and the line would render as an
    unstyled paragraph, which no render test can see."""
    sheet = _stylesheet()
    assert ".ss-card-metrics .ss-financial-caveat {" in sheet
    assert ".ss-health-block .ss-financial-caveat" not in sheet
    block = sheet.split(".ss-card-metrics .ss-financial-caveat {", 1)[1].split("}", 1)[0]
    assert "font-size: var(--ss-caption-size)" in block
