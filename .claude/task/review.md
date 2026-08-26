# Review

diff_sha256: 2e89b2d9f48761174aae0aed7dc3a37e076d4661597d2b86e6b8dab1b1d41282

Eight rounds, five reviewers. Required by routing: scope-auditor (always),
analytics-engineer-reviewer (`*.sql`, `*.csv`, `dbt_analytics/*.yml`), cto-reviewer
(`scripts/*`, `tests/*`, `frontend/*`), data-engineer-reviewer (`supabase/*`) and
equity-analyst-reviewer (`*metric_catalogue.csv`, `docs/data_contract.md`).

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role definition
verbatim first. Same role text, same cold blinded input, read-only.

**Verdict provenance, stated plainly because the hash moved between them.** The final hash
carries scope-auditor's round-8 verdict. The other four passed on earlier hashes:
data-engineer at round 1 (its findings were the `double precision` type and the two stale
eligibility mirrors, all fixed immediately), analytics-engineer and cto-reviewer at round 2,
equity-analyst at round 3. Everything staged after their respective passes was documentation
text and contract amendments -- no SQL, Python, seed, migration or test assertion moved, which
scope-auditor verified explicitly in rounds 7 and 8. Round 8's finding was this trail itself:
the amendments log claimed the stale-prose tail closed at round 6 when round 7 had found four
more sites. Corrected in the same commit.

**The three findings worth remembering:**

1. **Dropping `forward_pe` from the catalogue would have crashed the live app** (scope-auditor,
   round 1). `frontend/metric_school.py` rendered a "P/E" playground as tab 0 of the "Understand
   these numbers" panel and looked the metric up in `METRIC_LABELS`, built from the generated
   metrics.json -- a KeyError on every card that opened the panel. pytest stayed green because
   the tests imported only the seed helpers and never touched the render path. The playground is
   removed and a guard test now scans that file for label lookups and checks each id against the
   catalogue.
2. **The local `dbt build` passed vacuously** (analytics-engineer, round 1). Not one row in the
   35-row CI fixture set had a null `forward_pe`, so the eligibility change -- the whole point of
   the branch -- was exercised by nothing. A unit test now pins all three newly-admitted paths
   and fails on revert.
3. **The `net_cash` copy drafted here was financially wrong** (equity-analyst, round 1). The
   analogy said net cash is "what is actually yours", which describes equity; the learn text said
   a company "could repay every borrowing today", when `stmt_total_debt` excludes payables and
   `stmt_cash_and_equivalents` is the narrow row excluding short-term investments -- where young
   companies actually hold their money, so the claim could be flatly false for exactly this
   metric's population. The same wording sat in the LLM brief, instructing the model to write it
   onto live cards. Rewritten with both limits stated.

**The process lesson, also recorded in the contract:** seven of the eight rounds turned on stale
prose, surfacing one or two sites at a time, because each sweep searched for the metric ids and
not for the things said ABOUT them -- counts ("all 16", "the five metrics"), lens lists, "card
range mark", worked examples, playground inventories. One round also applied a fix to the wrong
row: a generic anchor matched twice and marked `roa_pct` as no longer catalogued when it is
still on the bank card. Reverted and reapplied.

**Open, recorded for the owner, NOT resolved here:** the `net_cash` user-visible copy; the
`READ_SYSTEM_PROMPT` rewording (§6 owner-signed content, two edits forced by the metric
removals); the pre-revenue verdict threshold collapsing from 0.2 to 0.0, which makes that axis
binary; the ~910+ Haiku regeneration on the next run; and the bank card's capital/asset-quality
blind spot, whose only disclosure now lives in non-deterministic LLM prose.

## scope-auditor
VERDICT: PASS
risks_checked:
- All 25 staged paths inside `scope_paths`; four separate widenings, each disclosed in an
  amendment and each confined to what the change genuinely reaches.
- Steps 2 and 3 (verdict redesign, sector-calibrated thresholds) genuinely not started.
- Owner-level decisions all recorded as pending rather than absorbed.
- Counts verified against the parsed seed (13 metrics, 10/3 direction split, 4 benchmarkable)
  rather than trusted from prose.
- Behavioural neutrality of the last three rounds confirmed: only description text and contract
  amendments moved.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `net_cash` SQL null-safe on both operands, correct layer placement.
- Seed parses to 13 rows x 21 columns with no quote-induced column shift; `frontend/metrics.json`
  byte-identical to the regenerated export.
- Eligibility mirrors in `_intermediate.yml`, `_marts.yml` and the singular export-contract test
  all state the same rule as the model.
- The new unit test exercises all three newly-admitted paths and fails on revert.
- `check_eligibility_baseline.py` gates drops only, so the intended rise cannot trip it.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `metric_school.py` removal complete; no other frontend module reads a dropped metric by key; a
  pre_revenue card renders correctly with `net_cash` absent entirely (the window between deploy
  and export).
- `INPUT_FIELDS_BY_TYPE` / `DIRECTION_BY_METRIC` / `READ_METRIC_BRIEF` mutually consistent with
  the catalogue, no orphan keys.
- The NaN-canonicalisation test was made vacuous by the diff and now mutates an in-set field.
- Full-deck Haiku regeneration traced and disclosed as owner-level cost.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Migration idempotent (`add column if not exists`), sorts after 012, picked up by
  `apply_supabase_migrations.py`, and its `--target dev` rewrite converts cleanly.
- No GRANT needed: table-level privileges from `011_grant_roles.sql` cover later-added columns;
  migration 012 is the precedent.
- `net_cash` added to `EXPORT_COLUMNS`; the export fails loudly (PGRST204), never silently, if
  the column is missing.
- `data-pipeline` runs migrations before the export, so the column cannot outrun its writer.
- Type corrected to `numeric`, matching every sibling metric column and the data contract.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Removing valuation and dividend yield is consistent with north_star's own rule that cards show
  fundamentals, not batch-pipeline prices; the verdict never read them.
- `net_cash` arithmetic matches the standard net-cash construction and the catalogue copy.
- The rewritten copy states both real limits and the scale warning, and the bias direction was
  verified against `ingestion/yfinance/balance_sheet.py` -- narrow cash understates.
- The false repayment claim reaches no user-visible surface and is out of the LLM brief.
- Pre-revenue green still asserts something real, but the axis is now binary -- disclosed.
- Bank card blind spot open and escalated, not silently carried.
