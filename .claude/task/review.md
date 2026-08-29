# Review

diff_sha256: 1a619fd57ac917c6470dd4b1c3bfeb898905f9bc05ca51c5c9be20182cfcb236

Two review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), cto-reviewer (`frontend/*`, `tests/*`). analytics-engineer-reviewer,
data-engineer-reviewer, and equity-analyst-reviewer are not routed to this diff's file set.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 2, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Shows each Discover card's own listing venue on its meta line ("{market} · {position} of
{total}", e.g. "FTSE 100 · 3 of 47"), so a reader meeting the same company twice across markets
(Shell, Rio Tinto, Block Inc, and nine others) can tell the two cards apart. Owner-approved via a
reviewed mockup (Option B: market leads, queue position follows). A new pure function
`card_venue_line()` in `frontend/explore_filters.py` replaces `walk_progress_line()` at the one
call site in `frontend/app.py`'s `_render_discover_tab`; Saved and Search were already correct
via an existing fallback and needed no change. `docs/north_star.md`'s Discover explore-model spec
is corrected (v2.3 -> v2.4): it previously documented the opposite rule.

Went through the project's UX PR gate (`docs/working_agreement.md`): north_star check, component
specs, and a live 480px browser smoke test (no horizontal scroll; company, sector, health
verdict, and first metric value all visible without scrolling; the market/position line correctly
varies per card when advancing the real queue, confirmed live against the running app, not
assumed from the CSS).

## Round-by-round findings and fixes

**Round 1**: cto-reviewer passed clean, confirming `card_venue_line`'s fallback delegates
correctly to `market_display_name` with no duplicated logic, `walk_progress_line` isn't
orphaned elsewhere, and the new tests are genuine (exact-string assertions that would catch a
swapped market/position order). scope-auditor failed on a real doc-sync gap outside the
original scope_paths: `docs/ui/discover_header.md` cited the retired "explore model v2.3" and
its "Belongs in header vs elsewhere" table still listed "walk position" and "market name on
card meta" as two separate facts, when the shipped code now unifies them into one line. Fixed:
the file added to scope_paths, its Authority line bumped to v2.4, and the table row reworded to
describe the single combined line.

**Round 2**: both required reviewers passed clean on a fresh, cold, independent pass.
cto-reviewer confirmed the doc's rendered-format example byte-matches what `card_venue_line`
actually produces, and diffed the frozen round-1/round-2 patches directly to confirm nothing
else drifted. scope-auditor ran its own broader doc-sync sweep across every file in `docs/` for
any other stale reference to the old rule, finding two other `v2.3` citations elsewhere in the
docs tree, correctly assessed as out of scope (one a dated point-in-time snapshot, the other
adjacent to an unrelated fact this task didn't touch). No further findings.

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-1 doc-sync gap is genuinely fixed, re-verified by reading the files directly: the
  Authority line matches `north_star.md`'s new heading, and the table no longer splits one fact
  into two rows.
- A broader sweep of every file under `docs/` for the old format or the old "not repeated on
  the card meta line" rule found nothing else needing a fix.
- `decisions_reserved` held in the actual code: Saved/Search call sites are untouched and still
  fall through to the existing market-only display; the new line is shown unconditionally, not
  gated on filter scope.
- No em/en dash on any added line, including the heading and table-row edits required by the
  version bump and rewording themselves.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `card_venue_line`'s fallback path delegates to `market_display_name` with no duplicated logic,
  so a missing or unknown market_code can't diverge between the two functions.
- The doc's claimed rendered-format example was checked against the actual function output, not
  just read as plausible prose.
- Diffed the frozen round-1 and round-2 patches directly to confirm only the flagged doc-sync
  fix changed and the previously-reviewed code/test surface is byte-identical.
