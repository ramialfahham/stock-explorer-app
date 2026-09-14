# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 8856beac593c6146fce4f40f41627647c88a2ba5d3954d8455bd176e33fdc5ed

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Two rounds.

## What shipped

The "What the numbers say - AI-written" card block no longer folds behind Read more/Show
less: `_health_block_html` renders it (and the deterministic verdict-meaning fallback) as an
always-visible bullet list, one `<li>` per sentence, via a shared `_bullets_html()` helper and
two new CSS classes (`ss-ai-read-list` / `ss-verdict-fallback-list`, styled identically, kept
distinct so the two stay distinguishable in the DOM). Sentence splitting is
`card_copy.py`'s new `ai_read_sentences()`.

"N saved" is now Saved-tab-only chrome (owner decision, 2026-09-14): Discover's list header
drops the " · N saved" suffix, Discover's card-open back row shows no count at all, and
Search never renders a saved-count line. `frontend/app.py`'s `_render_scope_stats` split into
`_render_discover_scope_stats` / `_render_saved_scope_stats`; `_render_back_row` takes
`saved_count: int | None`. docs/north_star.md, docs/ui/disclosure_pattern.md and
docs/ui/discover_header.md updated to match, including an honest note that a long AI read can
now push the first metric below the fold on a phone (not re-guarded).

718 tests (was 717; net +1 after replacing four fold-behavior tests with bullet-list ones and
adding sentence-split and Saved-tab-only-placement coverage).

## Round 1

scope-auditor: `ai_read_sentences()`'s split regex (`(?<=[.!?])\s+`) split inside abbreviations
-- "U.S. markets grew" became "U" / "S. markets grew". Fixed by adding a capital-letter
lookahead (`(?<=[.!?])\s+(?=[A-Z])`): text continuing after an abbreviation's period inside
the same sentence is not itself capitalized, so it no longer counts as a boundary. Regression
test added (`test_ai_read_sentences_does_not_split_inside_an_abbreviation`).

cto-reviewer: `docs/ui/disclosure_pattern.md` named a function, `_ai_read_bullets_html`, that
was never the real one -- the shared helper is `_bullets_html`. Doc corrected to the real name
and both real CSS classes.

## Round 2

scope-auditor: re-verified the regex fix against the round-1 example and the rest of the
checklist (scope_paths, decisions_reserved, done_when, doc sync). PASS.

cto-reviewer: re-verified the doc fix, grepped the repo for any other stale reference to the
invented function name (none found), reconfirmed `pytest tests/ -q` green. PASS.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

"N saved" placement: Saved-tab-only, over keeping it on Discover+Saved or de-duplicating it to
once-per-screen on all three tabs -- owner's choice, in chat, 2026-09-14.
