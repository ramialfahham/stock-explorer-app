# Discover: metric filters in Filters popover (Phase 2)

**Status:** Backlog (deferred from UX recovery v2.5)

## Summary

Extend the Discover **Filters** popover with optional filters on the five card metrics — e.g. min operating margin, max forward P/E.

## Context

Phase 1 (UX recovery v2.5) shipped market + sector only in the Filters popover. Metric filters were explicitly deferred per product choice.

## Acceptance criteria

- Filters popover includes metric range controls without cluttering the card face
- Filtering applies to Discover walk + browse pool (client-side on loaded cards)
- Update `docs/ui/discover_header.md` wireframe
- Tests for extended `filter_pool` metric predicates

## Related

- `frontend/explore_filters.py` — `filter_pool()`, `filter_scope_summary()`
- `docs/ui/discover_header.md`
