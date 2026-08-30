# Task contract

objective: Kill the landing screen entirely, per explicit owner decision (2026-08-30, after
  reviewing a mockup): no shrunk version, no replacement gate, no hints added to Discover. First
  launch goes straight into Discover. The brand and tagline a landing screen would show are
  already permanent in the header; the one thing on the old screen that wasn't shown anywhere
  else, "Not investment advice," becomes a permanent caption in the header instead of a one-time
  screen. This resolves `docs/backlog/landing_onboarding_rework.md`'s "blocking gate vs.
  progressive disclosure" and "what landing/onboarding each mean" open questions in favor of
  neither: no separate screen, no coach marks. It does not touch that doc's still-open
  "first-time Discover scope" question (the alphabetical, unfiltered, all-companies default
  stays exactly as it is; north_star's locked default is untouched).

scope_paths:
  - frontend/landing.py
  - frontend/app.py
  - frontend/browser_storage.py
  - frontend/overflow_menu.py
  - frontend/brand.py
  - frontend/styles.py
  - docs/ui/discover_header.md
  - docs/ui/design_system.md
  - docs/backlog/landing_onboarding_rework.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - tests/frontend/test_app.py

decisions_reserved:
  - **None of the actual design direction is reserved here**: the owner already decided (delete
    the screen, no replacement, disclosure becomes a permanent caption) after reviewing a
    mockup. What's reserved is catching every place the deleted mechanism is referenced, so nothing
    ships half-updated; that's a mechanical sweep, not a product decision, and is `done_when`'s
    job, not this section's.
  - **No test currently exercises any of this code.** Grepped `tests/` for `render_landing`,
    `onboarding_ready`, `is_onboarding_dismissed`, `dismiss_onboarding`, `request_landing`,
    `menu_how_it_works`, `LANDING_TAGLINE`, `ss-landing`: zero hits. Unlike the Discover
    walk-removal task, `pytest` will not catch a leftover reference to a deleted name; the sweep
    below has to be right by inspection, not backstopped by a test failure.
  - **Found during implementation: `frontend/app.py` has no existing test coverage at all,
    because `main()` runs unconditionally at module level** (`import app` executes the whole
    app). Splitting `_render_brand_header()` into a pure `brand_header_html()` (testable) plus a
    thin `st.markdown()` wrapper, per the plan agreed before implementation, required guarding
    the module-level call (`if __name__ == "__main__": main()`) so `tests/frontend/test_app.py`
    could import the function without executing the whole app. This is a real behavior change to
    `app.py`'s import semantics, not a pure refactor, so it needed real verification, not just
    reasoning: confirmed live, via the dev server, that `streamlit run frontend/app.py` (this
    repo's own dev launch config) still runs correctly with the guard, since Streamlit's script
    runner execs the target script inside a fake module named `"__main__"`.
  - **Found during implementation, and the reason the guard needed a second, separate
    verification: `streamlit_app.py` (repo root) is the actual deployed entrypoint** (its own
    docstring: "see render.yaml's startCommand"), and it does `import app` followed by an
    explicit `app.main()` call, a *different* pattern from the dev launch config. A stale
    historical note in `.claude/active_work.md` (from an old Slice 6b CDP-testing session)
    explicitly documents relying on `app.py` calling `main()` unconditionally on bare `import`;
    that assumption is now false. Traced why this still works: `import app` from
    `streamlit_app.py` gives `app.py`'s own module `__name__ == "app"` (standard Python import
    semantics, not the fake-`"__main__"`-module trick Streamlit applies to the *target* script),
    so the guard's condition is false and `main()` does NOT auto-run via the guard, exactly as
    before the guard existed for this entrypoint; `streamlit_app.py`'s own explicit `app.main()`
    call is what has always executed it. Verified live by actually starting
    `streamlit run streamlit_app.py` and confirming the rendered page matches the dev-config
    run exactly (brand header, disclosure, full list, no landing gate), not just reasoned through.
    The stale historical note is corrected in `.claude/active_work.md` (marked "UPDATED
    2026-08-30") rather than rewritten, since it's a dated record of a past session's own
    workaround, not live guidance to silently replace.
  - **Found during implementation: `docs/ui/design_system.md`'s "Overflow's three buttons" claim
    was already stale before this task**, from the earlier Discover rework removing the
    overflow menu's "Start over" button without catching this line. Re-counted the actual
    current overflow menu at implementation time rather than assuming either the old "three" or
    a guessed new number: exactly one button ("Clear saved") remains once this task's own
    "How Stock Explorer works" removal is applied.

done_when:
  - `frontend/landing.py` is deleted. `frontend/app.py` no longer imports or calls
    `render_landing`; `main()` goes straight from `ensure_interactions_loaded()` to
    `_discovery_page(client)`.
  - `frontend/app.py`'s brand header renders a third, permanent line under the tagline: the
    "Not investment advice" disclosure, in its own class (`ss-brand-disclaimer`), styled at
    caption weight, matching the tagline/caption tokens already used elsewhere in the header
    (not shouting, not the accent color). The header HTML-building is split into a pure
    `brand_header_html()` function (testable, returns a string) and a thin `_render_brand_header()`
    wrapper that calls `st.markdown()` on it, matching this codebase's existing
    `build_row_html()`/`render_row_list()` convention for exactly this kind of split.
    `frontend/app.py`'s module-level `main()` call is guarded
    (`if __name__ == "__main__":`) so the new pure function can be imported and tested without
    executing the whole app; both the dev launch config (`streamlit run frontend/app.py`) and
    the real deployed entrypoint (`streamlit_app.py`, which does `import app` then an explicit
    `app.main()`) are verified live, not just reasoned through, to still work correctly with the
    guard in place.
  - `tests/frontend/test_app.py` (new) unit-tests `brand_header_html()`: the disclosure text is
    present, and the three lines render in brand/tagline/disclosure order.
  - `frontend/browser_storage.py`: `ONBOARDING_KEY`, `_ONBOARDING_LOADED_FLAG`,
    `_load_onboarding_from_manager()`, `onboarding_ready()`, `is_onboarding_dismissed()`,
    `dismiss_onboarding()`, `request_landing()` are all removed, along with the two call sites
    inside `ensure_interactions_loaded()` (the `if not ... and manager.ready()` branch and the
    unconditional call after the first load). `ensure_interactions_loaded()` keeps working for
    interactions exactly as it does today; the manager-mount/ready machinery is shared
    infrastructure, not onboarding-specific, and stays untouched.
  - `frontend/overflow_menu.py`: the "How Stock Explorer works" button and its `request_landing`
    import are removed. Nothing replaces it; there is nothing left to replay once the screen it
    replayed no longer exists.
  - `frontend/brand.py`: `LANDING_TAGLINE` is removed (it was a bare alias to `PRODUCT_TAGLINE`
    with no other caller once `landing.py` is gone; confirm that at implementation time, not
    assumed here).
  - `frontend/styles.py`: the `.ss-landing*` rule block is removed. A new, small rule for the
    header disclosure caption is added, sized and colored like the existing caption tokens
    (`--ss-caption-size`, `--ss-caption`/`--ss-muted`), not a new visual weight.
  - `docs/ui/discover_header.md`'s "Vertical order" wireframe and block table gain the
    disclosure as its own numbered block (3, between Tagline and Nav), renumbering the blocks
    after it; the "What belongs in the header" table and 480px checklist mention it too.
  - `docs/ui/design_system.md`: the "Button variants" prose (currently "Landing's 'Start
    exploring', Overflow's buttons, and the Discover action bar all render identically") and the
    480px smoke bullet ("Landing's 'Start exploring' and Overflow's three buttons...") are
    corrected to drop the Landing reference and match the overflow menu's actual current button
    count: one ("Clear saved"), confirmed by re-count, not assumed from the old prose.
  - `docs/backlog/landing_onboarding_rework.md`'s Status line records the decision and links to
    this branch; the "Blocking gate vs. progressive disclosure" and "What landing and onboarding
    each mean" open questions are marked resolved with the answer (neither: no screen, no
    hints), not left reading as still-open. The "First-time Discover scope" and "What 'getting
    to the cards' should concretely become" questions stay open and unresolved: this task does
    not answer them.
  - **Found by round-2 cto-reviewer: the backlog doc initially violated the line above.** The
    first draft of the doc update marked "What 'getting to the cards' should concretely become"
    as resolved (reasoning: the existing card content already proves itself on tap, so no
    scaffolding was needed), directly contradicting this same contract's own done_when, which
    names that exact question as one that must stay open. No amendment recorded the deviation.
    This was a real overreach, not a wording slip: reading "no hints needed for standard
    controls" as also answering "does the row-to-card path deliver enough" reinterprets one
    owner decision to cover a second question it was never asked to cover, exactly the kind of
    unilateral rule-extension the working agreement's §6 reserves to the owner. Fixed: the
    question is restored to "still open" in the backlog doc, with a note explaining why killing
    the landing screen removes one candidate cause without establishing the remaining path is
    good enough.
  - A full-repo grep (excluding `.venv`/`target`/`.git`) for `render_landing`, `ss-landing`,
    `LANDING_TAGLINE`, `onboarding_ready`, `is_onboarding_dismissed`, `dismiss_onboarding`,
    `request_landing`, `menu_how_it_works`, and `How Stock Explorer works` returns nothing live
    outside dated/archival docs (`docs/handover_2026-08-18.md`, `docs/product_roadmap_2026-06.md`)
    and this task's own contract/review/backlog trail.
  - `pytest` green (418 passed, up from 416: two new `brand_header_html()` tests, no test
    removed since none existed for the deleted code). Live browser check against both the dev
    launch config and the real `streamlit_app.py` entrypoint confirms: first launch opens
    directly to Discover with no gate, the disclosure line is visible under the tagline with no
    horizontal overflow at 375px and no crowding of the nav row, and the overflow menu no longer
    offers "How Stock Explorer works."
  - No em dash or en dash on any added line.

impact_map:
  - Every visitor's first launch changes: no gate, straight into Discover. This affects 100% of
    first-time sessions, not a subset.
  - Deletes one whole module (`frontend/landing.py`) and roughly a dozen lines of
    localStorage-state plumbing (`frontend/browser_storage.py`) that exist for no other purpose.
  - Touches `frontend/app.py`'s module-level execution behavior (`main()` now guarded), which
    reaches the real production entrypoint (`streamlit_app.py`) as well as local dev; both were
    verified live, since a mistake here means the deployed app fails to render at all, not a
    cosmetic regression.
  - No dbt, ingestion, or data model change. Display/interaction only.

amendments: (none)
