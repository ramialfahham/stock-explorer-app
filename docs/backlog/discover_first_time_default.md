# Discover's first-time default scope

**Status:** Backlog. Flagged in `docs/backlog/landing_onboarding_rework.md`'s "Still open" list
(2026-08-30, after `feat/kill-landing-screen` merged) as a question deliberately not answered by
that decision. Scoped as its own item 2026-08-30.

## Summary

A visitor's first look at Discover today is the full, unfiltered, alphabetically-ordered list of
every card-eligible company (currently ~924 rows), because "All markets · All sectors" is
`north_star.md`'s locked default scope. Whether that's the right first thing to show, or whether
a smaller starting point would serve a newcomer better, is not decided here: this doc lays out
the current mechanism and the open questions that block writing a task contract with a locked
scope. Changing the default touches a locked north_star rule, which is a product decision
reserved to the owner regardless of the answer.

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

## Open questions (owner decisions, not answered here)

- **Does "first-time" mean anything worth building for, or should any change apply to every
  session uniformly?** The simplest version of "give newcomers a smaller starting point" is to
  just change the default for everyone, every time, no first-time detection at all. That's a
  real, much cheaper option worth considering before assuming a first-time-only default is what's
  wanted.
- **If it does need to be first-time-only, what counts as "first-time"?** Three options, in
  increasing order of cost and accuracy: (a) treat every fresh session as first-time (status
  quo, not actually first-time-only); (b) infer it from whether `interactions` is empty in
  localStorage, no new mechanism, but imprecise (a visitor who reads without ever saving or
  skipping looks "first-time" forever; clearing saved companies resets the signal); (c) add a
  dedicated persistent flag for "has visited before," a new mechanism requiring its own
  sign-off, and arguably the same category of machinery `feat/kill-landing-screen` just removed
  for being more than the job needed.
- **What would the smaller starting point actually be, if one is wanted?** A single market (which
  one, and picked how: the hero market, something registry-driven, something else)? A fixed-size
  curated set spanning markets/sectors? A random sample? Each implies different code and a
  different promise to the reader about what they're seeing and why.
- **Does this conflict with, or complement, the still-separately-open "getting to the cards"
  question** (`docs/backlog/landing_onboarding_rework.md`)? A smaller first list might make it
  easier to get to a card sooner, or might be an unrelated axis entirely; these shouldn't be
  assumed to have the same answer just because they're both about first impressions.
- **New mechanism.** Per the working agreement, any option beyond "change what
  `default_market_filter()` returns for everyone" is a new mechanism (new persisted state, a new
  heuristic reading existing state for a purpose it wasn't built for) and needs explicit owner
  sign-off, not something to add unilaterally once this item is picked up.

## Candidate directions (not decisions, for owner discussion)

1. **No change.** Keep "All markets · All sectors" for every session. Zero cost, matches the
   locked rule as it stands; doesn't address the concern if the owner still finds the full list
   intimidating for a newcomer.
2. **Change the default for everyone, not just first-time visitors.** Simplest real change:
   `default_market_filter()` returns something smaller (a market, a curated set) unconditionally.
   No new mechanism, but changes the experience for every session, including a returning
   visitor's, which may or may not be wanted.
3. **First-time-only, inferred from empty `interactions`.** No new persisted state; reuses what
   already exists. Imprecise in the way described above.
4. **First-time-only, via a new dedicated flag.** Most accurate to the literal idea of
   "first-time," at the cost of a new mechanism this repo just finished removing a version of.

## Related

- `docs/backlog/landing_onboarding_rework.md`: the question this doc splits out from, and the
  "getting to the cards" question that may or may not be related.
- `frontend/explore_filters.py` (`default_market_filter`, `ALL_MARKETS`, `ALL_SECTORS`),
  `frontend/app.py` (`_init_state`, `EXPLORE_DEFAULTS_VERSION`).
- `frontend/browser_storage.py` (`ensure_interactions_loaded`, the only cross-visit persistent
  state that exists in this app today).
- `docs/north_star.md`'s "Discover: explore model" table, "Default scope" row: the locked rule
  any change here would need to amend.
- `feat/kill-landing-screen` (merged 2026-08-30): removed the one piece of state
  (`onboarding_dismissed`) that used to track "has this visitor been here before," though it was
  never wired to this default.
