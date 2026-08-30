# Review

diff_sha256: dfe1d4e8454e3fef670dd8e92c8735460d4bebc70e726e10b66f2b5791a8c8c1

Six review rounds. Required reviewers per routing (`.claude/review_routing.json`): scope-auditor
(always), cto-reviewer (`frontend/*`, `tests/*`). Rounds 4 onward also required
analytics-engineer-reviewer (`dbt_analytics/*.yml`) and equity-analyst-reviewer
(`docs/data_contract.md`), pulled in once the diff grew to touch those paths.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first (from the plugin cache, except `equity-analyst-reviewer.md`, which this repo
keeps in its own tree at `.claude/agents/`). Cold, blinded, read-only input; the staged index
was frozen to a patch file and sha256 before every dispatch and never moved while reviewers
were running.

**Final verdicts (round 6, the commit gate):** scope-auditor PASS, cto-reviewer PASS,
analytics-engineer-reviewer PASS, equity-analyst-reviewer PASS.

## What this is

Reworks Discover from a one-card-at-a-time walk (filters that changed an invisible queue with
no visible effect) into filter -> scrollable list -> tap-to-focus, mirroring the pattern Saved
already uses. Every filtered match now renders as a row (company, ticker, sector, health
verdict, one type-aware lead metric); tapping a row opens the existing focus card. The walk
mechanism (`discovery_queue.py`, `queue`/`queue_index`/`market_index`/`sector_shown` state, the
"Next company" and "Start over" buttons, `card_venue_line()`) is fully retired, not kept as a
dead parallel path. Owner-approved via a reviewed mockup (Variant B: verdict + one lead metric
per row); "Not now" resolved to log-only with no visible list effect, since there is no walk
position left to deprioritize it from. Full detail, decisions, and found-during-implementation
items are in `.claude/task/contract.md`.

## Round-by-round findings and fixes

**Round 1**: scope-auditor found four stale references to the retired walk, one an actively
broken link: `docs/north_star.md`'s "What we are building" overview and "Out of scope for v1"
list still described "filter + walk" and a removed browse-list expander; `docs/ui/design_system.md`'s
480px checklist compared a button's skin to "Next company," a button this diff deletes;
`README.md` (outside the original `scope_paths`, added here) linked to `frontend/discovery_queue.py`,
which this diff deletes. All four fixed.

**Round 2**: scope-auditor found two more, one hop from a file round 1 had just fixed:
`docs/ux_principles_finanz_lern_apps.md` (linked directly from `north_star.md`) still described
the retired round-robin/hero-start walk and stated "No browse list," the opposite of what ships;
`docs/backlog/discover_metric_filters_phase2.md`'s acceptance criteria referenced a "Discover
walk pool" that no longer exists. Both fixed. Also found on a further self-initiated sweep, past
what either review round asked for: `frontend/markets.py`'s `discover_pool_summary()` rendered a
**live, user-visible** string in the overflow menu describing the retired walk's traversal
order ("{market} first, then rotating worldwide"), not a doc. Corrected to state the hero
market's count as a fact with no ordering claim.

**Round 3**: cto-reviewer caught a regression in round 2's own fix: the corrected
`discover_pool_summary()` asserted an unverified superlative ("the largest market") not checked
against actual data. scope-auditor independently found the eligibility gate's own documentation
still named the retired mechanism in four places, one of which (`docs/data_contract.md`) a
round-1 reviewer had explicitly read as generic and passed: `docs/data_contract.md`,
`dbt_analytics/models/_docs.md`, `dbt_analytics/models/5_marts/_marts.yml`, and
`dbt_analytics/models/4_intermediate/_intermediate.yml` all described `is_card_eligible`'s
still-active downstream effect as "discovery queue." The round-3 reading (a live description of
an in-use column naming a deleted mechanism) is the one acted on; all four corrected to
"discover pool." This pulled `analytics-engineer-reviewer` and `equity-analyst-reviewer` into
the required-reviewer set from round 4 on, since routing is computed from staged paths.

**Round 5**: with all four reviewers now dispatched, scope-auditor and equity-analyst-reviewer
independently identified the same substantive defect, not a doc-sync gap this time but a flaw
in the feature's own mechanism: the lead-metric mapping used `statement_roe_pct` (Return on
equity) as the Discover list row's lead metric for **both** `operating` and `financial`
company types. Checked against `scripts/assessment_rules.py:159-180` (`_verdict_operating`),
`statement_roe_pct` is only one of three **supporting** axes there ("Supporting axes may be
null; they can break a tie but never rescue a red flag," that function's own comment), never one
of the three **core** axes (`net_debt_to_ebitda`, `ebit_margin_pct`, `fcf_margin_pct`) that alone
decide red/green. The claim that it was "a direct input to the verdict rule" held for
`financial` (co-primary in `_verdict_financial`) but not for `operating`, the majority company
type. The owner was presented three options (keep ROE for both and accept the weaker claim, drop
the lead metric for operating entirely, or split by type) and chose to split by type:
`ebit_margin_pct` (Operating margin (TTM)) for operating, `statement_roe_pct` unchanged for
financial, `cash_runway_months` unchanged for pre_revenue.

**Round 6 (final)**: the split-by-type fix applied to `frontend/card_copy.py`
(`_LEAD_METRIC_BY_TYPE`, `lead_metric_for_row()`), its tests (`tests/frontend/test_card_copy.py`),
and every doc that stated the old mapping (`docs/north_star.md`'s "List row" rule,
`docs/ui/discover_list.md`'s lead-metric table and wireframe, `.claude/task/contract.md`,
`README.md`'s "Filter, then browse" bullet). All four required reviewers ran a fresh, cold,
independent pass and passed clean, including an independent equity-analyst-reviewer check of
whether `ebit_margin_pct` was genuinely the best of the three core axes (confirmed: it is the
only one of the three with `importance_tier: 1` in the metric catalogue) rather than a
rubber-stamp of the owner's choice.

## scope-auditor
VERDICT: PASS
risks_checked:
- Label/format correctness of the new mapping cross-checked against `frontend/metrics.json`:
  `ebit_margin_pct` -> "Operating margin (TTM)" / `percent_1`, `statement_roe_pct` -> "Return on
  equity" / `percent_1`, `cash_runway_months` -> "Cash runway" / `ratio_1`: the test assertions
  match what the code actually produces, not a guess.
- `DEFAULT_COMPANY_TYPE = "operating"` still matches the missing-type test's expectation after
  the split; the default case wasn't left pointing at stale behavior.
- Whole-repo sweep (excluding `.venv`/`.git`/`target`) for "Return on equity" and
  `statement_roe_pct`: every remaining hit outside this task's scope is either unrelated or an
  already-correct case (`docs/data_contract.md`'s "supporting (tie-breakers)" line,
  `docs/handover_2026-08-18.md`'s dated archive). No file still claims ROE is operating's lead
  metric.
- The analytical claims underlying the fix were verified against the actual code, not taken on
  faith: `_verdict_operating`'s `core`/`supporting` split and `_verdict_financial`'s
  co-primary ROE check both hold exactly as claimed; `ebit_margin_pct` is the only one of the
  three core operating axes with `importance_tier: 1`.
- Scope: every touched file is listed in the contract's `scope_paths`; nothing drifted outside
  it. Exactly one `_LEAD_METRIC_BY_TYPE` definition and one non-duplicated set of
  `lead_metric_for_row` tests survive, no stale test left asserting the old mapping.
- No em/en dash on any added line, scanned programmatically across the full patch.
- Both hash checks passed: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch are identical: the
  staged index did not move during review.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Every factual claim in `lead_metric_for_row`'s docstring checked line-by-line against
  `scripts/assessment_rules.py:159-198`: the core-axis list, the quoted "can break a tie but
  never rescue a red flag" comment, and `_verdict_financial`'s co-primary ROE check all hold
  exactly, no overstatement.
- New test assertions in `test_card_copy.py` pin real formatted output (`"1.0%"`, `"1.0"`)
  derived from the catalogue's actual `format`/`label` columns, not tautological checks.
- Grepped `frontend/` and `tests/` for any other code path or test still assuming ROE for
  operating: none found.
- `frontend/row_ui.py`'s existing `render_row_list`/`build_row_html` confirmed byte-identical
  to before this task; Saved/Search are untouched.
- No new dependency, service, or lifecycle hook introduced by this round's fix.
- No em/en dash on any added line.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Confirmed this round's fix touched no dbt file beyond the round-3 "discover pool" wording
  correction already accounted for; a frontend metric-selection fix could not silently carry a
  dbt change, and didn't.
- `ebit_margin_pct`, `statement_roe_pct`, and `cash_runway_months` are real, already-exported
  mart columns (`_marts.yml` lines 78/101/134) with descriptions consistent with the contract's
  eligibility claims: the frontend fix selects an existing upstream column, it doesn't invent
  or compute a new metric in the display layer.
- `dbt build --project-dir dbt_analytics --profiles-dir . --full-refresh`: 122/122 pass, 0
  errors/warnings.
- No em/en dash on any added `dbt_analytics/*` line.
- Non-blocking style nit (not grounds for FAIL): `_marts.yml` capitalizes "Discover pool" while
  the other three round-3-corrected locations use lowercase "discover pool."

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Independently verified `ebit_margin_pct` is a true core axis for `_verdict_operating` (not
  just "a" core axis but the best of the three by the one verifiable criterion available: it is
  the only one of `net_debt_to_ebitda` / `ebit_margin_pct` / `fcf_margin_pct` with
  `importance_tier: 1` in the metric catalogue, and the lowest `display_order` of the three).
- Re-verified `statement_roe_pct` remains correctly co-primary for `financial` and that nothing
  in this round's patch touches `scripts/assessment_rules.py` at all.
- Confirmed `docs/data_contract.md` needed no change for this fix: its existing
  verdict-methodology section already described `statement_roe_pct` as "supporting
  (tie-breakers)" for operating, consistent with the corrected mapping before this fix even
  landed.
- Checked every rewritten justification (docstring, test comment, `north_star.md`,
  `discover_list.md`) against the cited source verbatim: no overstatement or understatement.
- No em/en dash on any added line across the full patch.
