# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 40416f1f359668f4f8ccc3484fbcc51e6221f1cc0e78d4fce980ec641d62857a

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Two rounds on the original change; three more on a same-session addendum (below).

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
docs/ui/discover_header.md updated to match.

**Addendum, same session:** removing the fold left `docs/north_star.md`'s "first metric value
above the fold" mobile success check contradicted by the now-always-full read. Owner decided
(2026-09-14) to retire that check entirely rather than re-guard it. Swept:
`docs/north_star.md`, `docs/working_agreement.md`'s "480px smoke" item,
`docs/ui/discover_header.md` (two locations), `docs/ui/disclosure_pattern.md`,
`docs/product_roadmap_2026-06.md`'s live "Verification checklist" (its dated "Success
criteria" table left alone -- a point-in-time snapshot, not a living check),
`tests/frontend/test_app.py`'s docstring, and two code comments (`frontend/styles.py`,
`frontend/app.py`).

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

## Round 3 (addendum)

scope-auditor: PASS -- verified the retirement sweep's scope_paths and that the affected
doc/comment locations no longer assert the retired check as active.

cto-reviewer: FAIL. `docs/product_roadmap_2026-06.md`'s live "Verification checklist" item
still asserted the retired check (missed -- distinct from that file's dated, frozen "Success
criteria" table, which was correctly left alone). `tests/frontend/test_app.py`'s docstring
made the equivalent stale claim. `docs/working_agreement.md`'s edited "480px smoke" line
carried two em-dash characters forward from the pre-edit text -- this repo's "no em-dash on
any line you add or edit" rule applies even to characters not newly typed once the line is
touched. All three fixed.

## Round 4 (addendum)

cto-reviewer: FAIL. The round-3 fix to `docs/working_agreement.md` had appended a dated
narrative parenthetical -- `(owner decision, 2026-09-14, made when the AI-written read
stopped folding)` -- to a durable checklist file: the exact anti-pattern this repo's own
working agreement (§2) prohibits, and the one MR !115 already burned six of eleven review
rounds on. Swept every durable doc touched this session for the same pattern (not just the
flagged line): `docs/north_star.md`, `docs/ui/discover_header.md` (two locations),
`docs/ui/disclosure_pattern.md` reworded to drop the date, using this repo's existing `(§6)`
decision-rights shorthand instead -- but the actual edit to `docs/working_agreement.md`
itself was never applied in that pass, a real miss caught only by re-reading the staged diff
directly in the next round, not by trusting the stated intent.

scope-auditor: PASS (parallel round, before the working_agreement.md miss was caught).

## Round 5 (addendum, `docs/working_agreement.md` actually fixed this time)

scope-auditor: PASS. cto-reviewer: PASS -- re-read the staged diff directly, confirmed the
dated parenthetical is gone and the other four locations are still correctly fixed.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

"N saved" placement: Saved-tab-only, over keeping it on Discover+Saved or de-duplicating it to
once-per-screen on all three tabs -- owner's choice, in chat, 2026-09-14.
