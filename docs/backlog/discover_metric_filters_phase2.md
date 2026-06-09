# Discover: metric filters in Filters popover (Phase 2)

**Status:** Backlog (shipped in #117, reverted — popover too long on mobile; min/max defaults unclear; Clear crashed session state)

## Summary

Extend the Discover **Filters** popover with optional filters on the five card metrics — e.g. min operating margin, max forward P/E.

## Context

Phase 1 (UX recovery v2.5) shipped market + sector only in the Filters popover. Metric filters were deferred per product choice; a min/max popover attempt (#117) was reverted after mobile UX and Streamlit widget issues.

## Revisit criteria

- Fits on a phone without scrolling inside the popover (e.g. one metric at a time, presets, or separate screen)
- Clear “no filter” state without sentinel bounds (-500, etc.)
- No session-state writes after widgets are instantiated

## Acceptance criteria

- Filters popover includes metric range controls without cluttering the card face
- Filtering applies to Discover walk + browse pool (client-side on loaded cards)
- Update `docs/ui/discover_header.md` wireframe
- Tests for extended `filter_pool` metric predicates

## Related

- `frontend/explore_filters.py` — `filter_pool()`, `filter_scope_summary()`
- `docs/ui/discover_header.md`
