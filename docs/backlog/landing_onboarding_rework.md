# Landing page and onboarding rework

**Status:** Decided and implemented 2026-08-30, `feat/kill-landing-screen`. Flagged by the owner
during the Discover filter-list-focus work (2026-08-29): "the whole first impression and
onboarding... currently it is just not good." The one-card-mechanism half of that complaint is
fixed (`feat/discover-filter-list-focus`, MR !58, merged 2026-08-30). This doc originally scoped
the remaining half as open questions (2026-08-30); most were resolved the same day after
reviewing a live mockup, see "Decision" below. The remaining open questions are still genuinely
open and unaffected by this decision.

## Summary

The app's first-run experience, what a new visitor sees before they've done anything, needed a
rework: the owner decided to delete the landing screen entirely (see "Decision" below). The
"Context" section below describes the state that motivated that decision, as it existed when
this doc was first scoped, not the current implementation.

## Context

**What existed before this decision**, read directly from the code at the time, not assumed:

- `frontend/landing.py`'s `render_landing()` is a full-screen, blocking gate shown once on a
  visitor's first session (localStorage flag `onboarding_dismissed`), or replayed on demand from
  the overflow menu's "How Stock Explorer works" button (`frontend/overflow_menu.py`,
  `request_landing()`). It shows: an eyebrow ("How it works"), the product name, a tagline, four
  static bullet points, a disclaimer, and one "Start exploring" button. Dismissing it (either
  path) hides it; nothing else on the page renders underneath while it's shown.
- The four bullets were already mechanically corrected during the Discover rework to describe
  the shipped list mechanism ("Filter by market and sector, then browse the list and tap a
  company to learn more") -- that correction is done and out of scope here.
- Once dismissed, the first thing a visitor sees is: brand + tagline (`_render_brand_header()`),
  the Discover/Saved/Search nav, the Filters popover (closed, reading "All markets · All
  sectors"), the stats line, then the **full, unfiltered, alphabetically-ordered list of every
  card-eligible company** (currently ~924 rows) -- since "All markets · All sectors" is
  north_star's locked default scope.
- This app's own documented UX principle (`docs/ux_principles_finanz_lern_apps.md`, "Active user
  paradox"): "Beginners skip long tutorials. Learning happens through safe interaction... not
  static walls of text." The current landing screen is a static wall of text gating entry, which
  is in tension with that principle as written, not something this doc resolves.

**What the owner's complaint covered**, quoted directly: "The whole first impression and
onboarding. Specifically, the one card mechanism is ridiculous... I want you to think about a
better setup regarding landing page, onboarding and getting to the cards where learning content
is located." The one-card/filters-with-no-visible-effect part is fixed. "Landing page,"
"onboarding," and "getting to the cards where learning content is located" are three distinct
things the current single screen does not clearly separate, and this doc treats them as
possibly-separate problems rather than assuming they share one fix.

## Decision (2026-08-30)

After reviewing a live mockup comparing the current gate against candidate replacements, the
owner rejected coach-marks/hints as condescending for standard controls ("users don't need
hints to use filters. and they need no hints to tap on an entry") and then went further than any
of the three candidates below: **delete the landing screen outright, add nothing in its place.**
First launch goes straight into Discover. The brand and tagline it would have shown are already
permanent in the header; the one thing on it that wasn't shown anywhere else, "Not investment
advice," became a permanent caption in the header instead. No hints, no coach marks, no curated
first-time list. Implemented in `feat/kill-landing-screen`.

## Open questions

Resolved by the decision above:

- ~~What "landing" and "onboarding" each mean here~~: resolved as neither needs a separate
  screen. The one durable job a landing screen would do (brand, tagline, trust disclosure) is
  already covered by the always-visible header; no onboarding flow was added to replace it.
- ~~Blocking gate vs. progressive disclosure~~: resolved as neither. Standard controls
  (filters, list rows) don't get hints; nothing was added to Discover.
- ~~Replay path~~: resolved as a direct consequence. The overflow menu's "How Stock Explorer
  works" button is removed, since there is nothing left to replay.
- ~~New mechanism~~: moot, since this was a deletion, not an addition. No new mechanism was
  introduced.

Resolved separately, not by this decision:

- **First-time Discover scope.** Scoped as its own item 2026-08-30:
  [`docs/backlog/discover_first_time_default.md`](discover_first_time_default.md). Decided the
  same day: no change. The full unfiltered list stays for every visitor, every time; see that
  doc for why.

Still open, not touched by this decision:

- **What "getting to the cards where learning content is located" should become, concretely.**
  Genuinely not answered by this decision, despite the temptation to read it as implied. Killing
  the landing screen removes one candidate *cause* (a bullet list promising depth that's three
  taps away) but doesn't establish that the remaining path (list row -> focus card) actually
  delivers on that promise well enough. That's a real, separate product question, still open,
  and answering it here would have been reinterpreting one decision (delete the screen) to also
  cover a second one (the row-to-card path is good enough) it was never asked to cover.

## Candidate directions considered (historical, superseded by the decision above)

These were sketched as discussion starters before the decision. The actual outcome went further
than all three: no screen at all, not even a shrunk or split one.

1. **Minimal:** keep the single blocking landing screen; revise only its copy and visual weight.
   Smallest change; does not address the "static wall of text" tension with the app's own stated
   principle. Not chosen.
2. **Split:** a brief landing/hero moment answering "what is this," separate from progressive,
   inline onboarding hints that appear the first time a visitor reaches Discover. Not chosen:
   the owner rejected hints on standard controls as unnecessary once actually mocked up.
3. **Structural:** replace the blocking gate with a first-run state built into Discover itself
   (e.g. a small spotlighted set of companies instead of the full list on the very first visit).
   Not chosen: the first-time Discover scope stayed the locked default, untouched, separate
   from this decision.

## Related

- `frontend/landing.py` (deleted), `frontend/browser_storage.py`'s onboarding-state functions
  (`onboarding_ready`, `is_onboarding_dismissed`, `dismiss_onboarding`, `request_landing`, all
  removed)
- `frontend/overflow_menu.py`'s "How Stock Explorer works" button (removed, nothing left to
  replay)
- `docs/ux_principles_finanz_lern_apps.md`: "Active user paradox" and "Progressive disclosure"
- `docs/ui/discover_header.md`, `docs/north_star.md`'s "Audience and tone" section
- `feat/discover-filter-list-focus` (MR !58, merged 2026-08-30): fixed the structural half of
  the owner's original complaint (filters with no visible effect); `feat/kill-landing-screen`
  fixed the rest.
