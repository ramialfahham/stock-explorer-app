# Task contract

objective: Fix the Streamlit CSS-specificity bug (documented in MR #24, audited this
session) across the ~24 remaining bare single-class `<p>` selectors it affects — each was
silently losing its declared `font-size` (and, for one class, `margin-top`) to a
higher-specificity Streamlit emotion-cache ancestor rule, exactly like the classes MR #24
already fixed for the metric cell.

scope_paths:
  - frontend/styles.py
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_reserved:
  - (none) — this is item 1 of 2 already-listed "Next concrete actions" in active_work.md
    (flagged, not fixed, in MR #24's own Status entry); owner approved the audit, then
    approved proceeding with the fix, in two separate "go ahead"s this session.
  - No product/visual decision is made here: every fixed class keeps its EXISTING declared
    value (same font-size, same margin) — the bug was that the browser was silently
    discarding an already-decided value, not that the value itself was ever in question.
    Nothing here changes what anything looks like by design; it changes what actually
    renders to match what was already specified.

technical_definition: |
  Verified live (not just from the MR #24 code comment) via the browser's own computed
  styles and matched-rule inspection against the actual Streamlit emotion-cache stylesheet:
  a bare single-class `<p class="ss-foo">` selector (specificity 0,1,0) loses to Streamlit's
  own `.st-emotion-cache-<hash> p { font-size: inherit; ... }` rule (0,1,1) whenever that
  `<p>` is nested inside the matching ancestor -- which is effectively everywhere, since
  every `st.markdown(unsafe_allow_html=True)` call renders through one of these ancestors.
  A second, narrower Streamlit rule (`margin-top: 0; margin-left: 0; margin-right: 0;`, also
  0,1,1) additionally zeroes any NON-ZERO margin-top a bare class declares -- invisible for
  the ~23 classes that only ever set margin-bottom, but real for the one that doesn't
  (ss-saved-news-heading).

  Fix technique matches MR #24's own established pattern: scope each bare selector under its
  always-present parent class (e.g. `.ss-metric .ss-metric-label`, matching the already-fixed
  `.ss-metric .ss-metric-gloss`), pushing specificity to 0,2,0. For the handful of classes
  with no natural parent wrapper in the DOM (`ss-filter-summary`, `ss-saved-list-fresh`,
  `ss-saved-news-heading`, `ss-company-summary` short-form), used `!important` instead --
  already an established technique elsewhere in this same file (button/popover overrides),
  simpler than inventing a new wrapper `<div>` purely for CSS-specificity purposes.

  `ss-freshness` had a SEPARATE, unrelated bug: its intended scoped rule
  (`.ss-card-footer-shell + div[data-testid="stHorizontalBlock"] .ss-freshness`) never
  matched the real DOM at all (same root cause as the pre-Slice-6b stLinkButton/
  stBaseLinkButton-secondary testid mismatch) -- confirmed live via `element.matches()`
  against every stylesheet rule and a full ancestor-chain walk with real data-testid values.
  Fixed with the verified-correct selector
  (`[data-testid="stElementContainer"]:has(.ss-card-footer-shell) + [data-testid="stLayoutWrapper"] .ss-freshness`),
  same `:has()` + adjacent-sibling technique already used for the icon-button trigger rule
  later in the same file. The old bare `.ss-freshness { font-size: ...; color: ...; }`
  fallback rule (which is what was actually rendering, silently, since the scoped rule never
  fired) is removed as fully superseded now that the scoped rule works.

  `ss-benchmark-unavailable` and `ss-benchmark-note` are structurally the same kind of bare
  selector but were confirmed NOT to need this fix: `ss-benchmark-unavailable` declares
  neither font-size nor a non-zero margin (nothing for the bug to corrupt); `ss-benchmark-note`
  has zero Python call sites repo-wide (dead CSS) -- scoped anyway alongside its live sibling
  `ss-median-primer` so it doesn't reintroduce the bug if it's ever used.

  `ss-row-title`/`ss-row-sub` and the four classes MR #24 already fixed
  (`ss-metric-gloss`, `ss-metric-range-unavailable`, `ss-metric-group-heading` in both its
  contexts, `ss-metric-analogy`) were re-verified live as unaffected/already-correct --
  served as positive controls proving the scoping technique actually works before applying
  it to the rest.

  `ss-explain-all`/`ss-explain-list` (+ its `dt`/`dd` children)/`ss-header-pool`/
  `ss-market-breakdown*`/`ss-saved-fresh` are dead CSS (zero Python call sites, confirmed
  repo-wide) -- noted, not touched; `ss-saved-fresh` shares this bug's vulnerable shape
  (bare class, declares font-size) but nothing renders it, so nothing to fix; the other four
  aren't even `<p>` selectors.

  cto-reviewer round 1 found two real problems, both fixed and re-verified live before round
  2: (1) `ss-company-summary` (short/non-truncated description) had genuinely used
  `!important` on a false premise -- its own comment claimed "no wrapping ancestor class,"
  but `_company_summary_html()`'s return value renders inside the SAME `.ss-card-identity`
  section as `.ss-meta-line` two rules above it in every code path (both the truncated and
  non-truncated branches), so it should have been parent-scoped like everything else.
  Switched to `.ss-card-identity .ss-company-summary`, re-verified live by injecting a
  synthetic element into a real `.ss-card-identity` and reading its computed style (real
  card data with a short-enough description to hit this code path wasn't readily
  reproducible by browsing). (2) A second, PRE-EXISTING sibling-selector bug sitting two
  rules above the `ss-freshness` fix, same file, same root cause, not part of this task's
  original ~24-class list because it isn't a `<p>` selector at all:
  `.ss-card-footer-shell + div[data-testid="stHorizontalBlock"]` (the footer's top-border/
  spacing separator) matched zero elements for the identical reason `ss-freshness` did --
  `.ss-card-footer-shell` itself has no next sibling; the real sibling relationship is one
  level up, between its `stElementContainer` and the following `stLayoutWrapper`. Fixed with
  the same corrected pattern already worked out for `ss-freshness`
  (`[data-testid="stElementContainer"]:has(.ss-card-footer-shell) + [data-testid="stLayoutWrapper"]`),
  live-verified: the footer separator (a 1px top border above the Yahoo Finance link) now
  actually renders for the first time. Fixing this was judged in-scope despite not being
  part of the original ~24-class list -- same root cause, same fix, discovered as a direct
  byproduct of the DOM archaeology this task already required, three lines from a rule this
  diff was already touching; leaving a twin of a bug just fixed, right next to the fix,
  would have been the "spot-fixing one layer at a time" anti-pattern CLAUDE.md itself warns
  against.

explicitly_not_in_scope:
  - Deleting the dead CSS classes noted above (`ss-explain-all` etc.) -- separate cleanup,
    unrelated to this bug.
  - The sector min/max data-quality issue (Deep Yellow near-zero-revenue denominator) --
    the other item in active_work.md's "Next concrete actions", tracked separately.
  - Any visual/design change beyond making already-declared values actually render.

done_when:
  - All ~24 classes identified in the live audit show computed font-size (and, for
    ss-saved-news-heading, margin-top) matching their declared CSS value, re-verified live
    in the browser after the fix (not just inferred from the CSS source).
  - `ss-freshness`'s scoped selector confirmed to actually match the real DOM
    (`element.matches()`), not just assumed correct by construction.
  - Full test suite passes (`python -m pytest tests/ -q`).
  - 480px mobile smoke check: no horizontal scroll; company + sector + health verdict +
    first metric visible without scroll (per docs/working_agreement.md's UX PR gate).
  - `.claude/active_work.md`'s "Next concrete actions" updated to reflect this is done.

amendments:
  - 2026-08-24 — initial contract, written after the audit (Explore) and the fix
    (Implement) -- the audit itself was presented to and approved by the owner ("go ahead
    with the CSS audit first"), and the fix was separately approved after the audit report
    ("go ahead with the fix"), so both steps this contract covers were confirmed in
    conversation before being carried out, in the same pattern as the immediately preceding
    dead-code-cleanup task this session.
  - 2026-08-25 — cto-reviewer round 1 FAILed with two real findings (see
    technical_definition's new paragraph); both fixed and re-verified live, `ss-saved-fresh`
    added to the dead-CSS accounting per its "supporting observation." No owner escalation
    needed -- both were within the task's own already-approved objective (fix this specific
    Streamlit CSS-specificity bug pattern), not new decisions.
  - 2026-08-25 — scope-auditor round 2 correctly ESCALATEd whether fixing the footer-
    separator bug (a third, non-`<p>`, out-of-original-list instance of the exact same
    dead-selector root cause) was within the builder's own authority to decide, and whether
    a border rendering for the first time contradicts this contract's "no visual change"
    claim. Genuinely escalated to the owner (not self-answered) -- owner chose "fix all
    three": keep the footer-separator fix, and additionally fix the THIRD instance
    cto-reviewer's own round 2 found in the same pass (the Yahoo Finance link button's
    `stBaseLinkButton-secondary` sizing rule, same broken sibling-combinator prefix, same
    corrected pattern), which had been deliberately left untouched pending this answer.
    All three re-verified live after the fix (font-size/min-height/padding/text-decoration
    on the link button; border-top on the footer separator). scope_paths/objective NOT
    amended to retroactively describe these as originally in-scope -- they are documented
    here, honestly, as an owner-approved widening mid-task, not as something the original
    audit already covered.
