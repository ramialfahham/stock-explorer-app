# Discover's first-time default scope

**Status:** Decided 2026-08-30: no change. Flagged in
`docs/backlog/landing_onboarding_rework.md`'s "Still open" list (2026-08-30, after
`feat/kill-landing-screen` merged) as a question deliberately not answered by that decision.
Scoped as its own item 2026-08-30, then resolved the same day, see "Decision" below.

## Summary

A visitor's first look at Discover today is the full, unfiltered, alphabetically-ordered list of
every card-eligible company (currently ~924 rows), because "All markets · All sectors" is
`north_star.md`'s locked default scope. That stays exactly as it is: see "Decision" below for why.
The "Context" and "Open questions" sections describe the state this doc was originally scoped
against, before that decision.

## Context

**What exists today**, read directly from the code, not assumed:

- `frontend/explore_filters.py`'s `default_market_filter()` always returns `ALL_MARKETS`; there
  is no branching logic anywhere for a different default under any condition.
- `frontend/app.py`'s `_init_state()` applies that default to `st.session_state["explore_market"]`
  /`explore_sector"]` on every fresh session, and force-reapplies it whenever
  `EXPLORE_DEFAULTS_VERSION` is bumped in code (a cache-bust mechanism for *changing the default
  in a future release*, not a per-visitor "have you been here before" flag).
- **"First-time" is a looser idea than it sounds, given how session state actually works.**
  Streamlit's `st.session_state` doesn't persist across a page reload or a new tab; only the
  `interactions` list (Save/Not now) persists, via browser localStorage
  (`frontend/browser_storage.py`). So today's default scope isn't really "shown once, to
  newcomers": it's "shown every time a session starts," to anyone, on every visit, whether
  they've saved forty companies already or none at all. There is currently no code path that
  distinguishes a true first-ever visit from someone's hundredth session.
- **This matters more than it otherwise would because the mechanism that used to carry that
  distinction was just deleted.** `feat/kill-landing-screen` removed `onboarding_dismissed` and
  the rest of the landing-screen's session-tracking state (`docs/backlog/landing_onboarding_rework.md`).
  That flag was never wired to the Discover default (it only gated the old landing screen), but
  it was the one piece of state in this codebase that meant "this visitor has been here before."
  It no longer exists. Any version of "first-time default" that means something more precise
  than "every session" needs a signal that isn't currently in the codebase at all.
- `north_star.md`'s "Discover: explore model" table (line 126) states the locked rule: "Default
  scope | **All markets · All sectors**" followed by a parenthetical comparing against "the full
  mixed worldwide queue." That parenthetical compares against the retired walk mechanism's
  "queue" framing, which reads a little stale now that Discover is list-based, not something
  this doc fixes on its own initiative.

## Decision (2026-08-30)

**No change. The full, unfiltered list stays on first load, for every visitor, every time.**
Candidate direction 1 below, chosen outright.

The premise behind scoping this as a problem was wrong: it treated "new to reading financial
statements" and "new to using a web app" as the same kind of beginner. This app is for the
former, not the latter. Someone who doesn't yet know what a P/E ratio means can still use a
filter dropdown or a search box without any trouble; a long browsable list plus filter and
search is the standard, correct pattern for this, not something that needs softening for a
first-time visitor. Reducing the list would have solved a problem this app's actual audience
doesn't have.

Discover's market/sector filters already exist. Free-text search by company name also already
exists, as its own "Search" tab, separate from Discover. That covers the "filter or search
directly by company name" mechanism this decision leans on; no new filter or search capability
was built or is needed to make this decision sound.

**Not decided here, a separate, optional idea:** whether name search should be available
directly on Discover (not just its own tab), so a visitor who knows what they're looking for
doesn't have to switch tabs. Floated in the discussion that led to this decision, not scoped or
committed to.

## Open questions

All resolved by the decision above; kept for the record, not because they're still open:

- ~~Does "first-time" mean anything worth building for, or should any change apply to every
  session uniformly?~~ Resolved: no first-time distinction is needed at all, because no change
  to the default was needed in the first place.
- ~~If it does need to be first-time-only, what counts as "first-time"?~~ Moot: nothing
  first-time-specific is being built.
- ~~What would the smaller starting point actually be, if one is wanted?~~ Moot: there is no
  smaller starting point.
- ~~Does this conflict with, or complement, the still-separately-open "getting to the cards"
  question?~~ Moot for this decision specifically, since nothing changed here to compare it
  against. Whether the two questions actually relate is not decided by this doc either way; that
  question (`docs/backlog/landing_onboarding_rework.md`) stays open on its own.
- ~~New mechanism.~~ Moot: nothing beyond the existing filters and the existing Search tab was
  needed.

## Candidate directions considered (historical, superseded by the decision above)

1. **No change.** Keep "All markets · All sectors" for every session. **Chosen.**
2. **Change the default for everyone, not just first-time visitors.** Not chosen: no problem
   established that this would have solved.
3. **First-time-only, inferred from empty `interactions`.** Not chosen, for the same reason.
4. **First-time-only, via a new dedicated flag.** Not chosen, for the same reason; would also
   have reintroduced a version of the machinery `feat/kill-landing-screen` just removed.

## Related

- `docs/backlog/landing_onboarding_rework.md`: the question this doc splits out from, and the
  "getting to the cards" question that may or may not be related.
- `frontend/explore_filters.py` (`default_market_filter`, `ALL_MARKETS`, `ALL_SECTORS`),
  `frontend/app.py` (`_init_state`, `EXPLORE_DEFAULTS_VERSION`).
- `frontend/browser_storage.py` (`ensure_interactions_loaded`, the only cross-visit persistent
  state that exists in this app today).
- `docs/north_star.md`'s "Discover: explore model" table, "Default scope" row: the locked rule
  this decision leaves untouched.
- `feat/kill-landing-screen` (merged 2026-08-30): removed the one piece of state
  (`onboarding_dismissed`) that used to track "has this visitor been here before," though it was
  never wired to this default.
