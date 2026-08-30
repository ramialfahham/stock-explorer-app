# Landing page and onboarding rework

**Status:** Backlog. Flagged by the owner during the Discover filter-list-focus work
(2026-08-29): "the whole first impression and onboarding... currently it is just not good."
The one-card-mechanism half of that complaint is fixed (`feat/discover-filter-list-focus`,
MR !58, merged 2026-08-30). This doc scopes the remaining half: the landing screen and
onboarding flow themselves. Scoped as its own item 2026-08-30.

## Summary

The app's first-run experience, what a new visitor sees before they've done anything, and how
they're helped toward their first useful action, needs a rework. What that rework should
actually be is not decided here: this doc lays out the current state and the open product
questions that block writing a task contract with a locked scope.

## Context

**What exists today**, read directly from the code, not assumed:

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

## Open questions (owner decisions, not answered here)

- **What "landing" and "onboarding" each mean here**, since today one screen conflates them. A
  landing page (what the app *is*, for someone deciding whether to use it) and onboarding
  (helping a first active user succeed at their first task) are different jobs with different
  content and different failure modes. Should this rework keep them as one screen, or split
  them, e.g. a brief "what this is" moment versus progressive, inline hints inside Discover
  itself?
- **Blocking gate vs. progressive disclosure.** Keep a single blocking "Start exploring" screen
  (today's shape, already copy-correct for the shipped list), or move toward contextual guidance
  (e.g. a first-visit hint on the Filters popover, or a nudge that a row opens a full snapshot),
  dismissible per element rather than as one gate? The latter follows this app's own "Active
  user paradox" principle more closely but is a materially bigger structural change than the
  former.
- **First-time Discover scope.** A first-time visitor lands on the full unfiltered ~924-company
  list today. Is "everything, alphabetically" still the right first thing to show (north_star's
  existing, locked "All markets · All sectors" default), or does a first-time visitor need a
  smaller suggested starting point to avoid an intimidating wall of names? Changing the default
  scope itself would need its own owner sign-off separate from this doc, since it's a locked
  north_star rule.
- **What "getting to the cards where learning content is located" should become, concretely.**
  Is the concern that a first-time visitor doesn't realize a company row opens a full analytical
  snapshot with metric definitions, benchmarks, and playgrounds (an awareness/copy problem,
  fixable in the landing screen or an inline nudge), or that too many taps separate landing from
  that content (a navigation/information-architecture problem)? These have different fixes.
- **Replay path.** "How Stock Explorer works" in the overflow menu replays the exact same
  first-run screen today. If the first-run shape changes, does the replay stay a fixed reference
  screen, or does it need to change too?
- **New mechanism.** Per the working agreement, anything beyond a copy/layout change to the
  existing screen and flow (a persistent progress tracker, a multi-step wizard, a coach-mark/
  tooltip library, an analytics/funnel hook) is a new mechanism and needs explicit owner
  sign-off before being added, not something to introduce unilaterally once this item is picked
  up.

## Candidate directions (not decisions, for owner discussion)

1. **Minimal:** keep the single blocking landing screen; revise only its copy and visual weight.
   Smallest change; does not address the "static wall of text" tension with the app's own stated
   principle.
2. **Split:** a brief landing/hero moment answering "what is this," separate from progressive,
   inline onboarding hints that appear the first time a visitor reaches Discover (e.g. pointing
   at Filters, or a one-time nudge that a row opens a full snapshot).
3. **Structural:** replace the blocking gate with a first-run state built into Discover itself
   (e.g. a small spotlighted set of companies instead of the full list on the very first visit),
   with no separate screen at all.

## Related

- `frontend/landing.py`, `frontend/browser_storage.py` (`onboarding_ready`,
  `is_onboarding_dismissed`, `dismiss_onboarding`, `request_landing`)
- `frontend/overflow_menu.py`'s "How Stock Explorer works" replay button
- `docs/ux_principles_finanz_lern_apps.md`: "Active user paradox" and "Progressive disclosure"
- `docs/ui/discover_header.md`, `docs/north_star.md`'s "Audience and tone" section
- `feat/discover-filter-list-focus` (MR !58, merged 2026-08-30): fixed the structural half of
  the owner's original complaint (filters with no visible effect); this doc scopes the rest.
