# Review

diff_sha256: 5280941bdc7ae13732395cd187810ad87c46b0268ddc3745967656a612746574

Sixteen review rounds. Reviewers: scope-auditor (required, `always`), analytics-engineer-reviewer
(`*.sql`, `*.csv`, `*dbt_project.yml`), data-engineer-reviewer (`ingestion/*`, `supabase/*`),
cto-reviewer (`scripts/*`, `tests/*`, `frontend/*`), equity-analyst-reviewer
(`docs/data_contract.md`).

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold blinded input, read-only, index frozen before each dispatch.

**Final verdicts (round 16, the commit gate):** scope-auditor PASS, analytics-engineer-reviewer
PASS, data-engineer-reviewer PASS, cto-reviewer PASS, equity-analyst-reviewer PASS.

## What this is

Batch 2 of 3 in the market-onboarding queue: Netherlands (AEX), Switzerland (SMI), Spain
(IBEX 35). All eleven activation-checklist steps done for all three markets. 80 seed rows, 74
distinct new companies, deck grows by roughly 65 cards once the branch runs.

## The shape of the sixteen rounds

Rounds 1 through 6 fixed real code and data defects: the constituent-name cleaner
(`_clean_company_name`), the two collision guards (`KNOWN_DUAL_INDEX_SYMBOLS`,
`KNOWN_CROSS_MARKET_COMPANIES`), the within-market duplicate-headline guard
(`KNOWN_DUPLICATE_SEED_NAMES`), the CI eligibility-baseline guard, and the currency-mirror test.
Each of these is mutation-proven: the round-by-round record in the branch's commit history and
this file's predecessor drafts show the exact failing counts for each guard when weakened.

Rounds 7 through 16 found **zero further code defects**. Every finding from round 7 onward was
prose: the contract and the session handover contradicting each other, contradicting themselves,
or drifting out of sync with a guard that had itself just been corrected. The recurring failure
was fixing a claim in the file a reviewer named and leaving the identical claim standing in its
sibling (contract vs. handover vs. a code comment vs. a test docstring). Four separate rounds (7,
8, 12, 14) were single-class sweeps of exactly this problem after a reviewer caught one instance
and a second reviewer caught the same class surviving elsewhere. This is the intended purpose of
routing docs through the same review cycle as code: none of these sixteen rounds would have been
needed if the prose had been left as terse cross-references instead of restated facts, and that
is the lesson carried into `.claude/active_work.md` for the next batch.

## The two defects this branch found outside its own scope

Both are filed as separate tasks, not fixed here, because both edit already-shipped card content
under section 6.

- **Eleven of 116 `jp_nikkei225` seed rows carry the wrong company name**, found by widening the
  duplicate-headline guard past exact-string matching and then auditing the full seed against
  yfinance. Two are visible to the widened guard (their true owner is also a row in the seed);
  nine are not. `9101` "Mitsui O.S.K. Lines" is actually Nippon Yusen (NYK Line); the real Mitsui
  O.S.K. Lines is `9104`, one row down.
- **`au_asx200` ticker `XYX` for Block, Inc. is a one-keystroke error** (`XYZ` is correct); that
  row has fetched no data since the 2026-05-23 import, and nothing in the pipeline detects a
  constituent that resolves to zero fundamentals rows.

## Owner decisions recorded 2026-08-28

Four escalations, all answered, three creating separate work rather than changing this branch:

1. The 20-card warn threshold is wrong (compares an absolute count against 20-member indices).
   Deferred to phase 2 rather than changed here, per the working agreement's rule against
   weakening a gate on the branch it fails.
2. Currency rendering follows real-world practice: CHF stands as-is; CAD becomes `C$`; SEK, DKK,
   NOK stay ISO codes. No code change on this branch (both `_CURRENCY_SYMBOLS` copies verified
   unchanged, no CHF key added).
3. Seed name corrections move into a dbt model: a seed exposed via a staging pass-through, with
   the correction applied in `2_base` alongside `base_yf__constituents`. Explicitly does NOT cover
   the Block ticker, which is upstream of dbt entirely (`ingestion/yfinance/ingest.py:309-314`
   reads the CSV ticker column before dbt runs). Filed separately with the design questions this
   branch surfaced: `check_layer_contract.py` requires staging SQL under `1_staging/<source>/`,
   `_yfinance_staging.yml:32` will need its "overridden in core" line corrected, and the missing
   seed-versus-fundamentals detector belongs in the same contract.
4. Duplicate cards (13 companies, six pre-existing) stay; every card will show its listing venue.
   Deferred to its own UX-gated branch; does not by itself correct the two deck-wide counters that
   say "companies" while counting listings.

## Verification

- pytest 391 passed. `dbt build --full-refresh` 108/108. Five credential-free CI gates green
  (`check_layer_contract`, `check_registry_var_sync`, `check_dbt_tests`, `check_dbt_documentation`,
  `check_dbt_sql_structure`). `check_eligibility_baseline` OK at 63 = 9 markets x 7 fixture rows.
- No em dash or en dash on any added line across the full patch (scanned programmatically every
  round, confirmed again at the frozen commit-gate diff).
- Guard mutation proofs (reproduced independently by multiple reviewers across rounds): the
  duplicate-headline guard's widened key fails on reverting to exact matching; the marker-class
  guard fails 16/21 cases when neutered; the currency-mirror test fails when either
  `_CURRENCY_SYMBOLS` copy drifts; the CI baseline guard fails on a stale per-market count.
- No seed was hand-corrected in anticipation of decision 3; no card-face change landed despite
  decision 4 being approved; no gate threshold was touched despite decision 1.

## scope-auditor

Sixteen rounds, FAIL through round 15, PASS at the commit-gate round (16). Blocking findings
across the cycle: truncated bullets from in-place edits (rounds 5, 12), a `scope_paths` list that
drifted out of sync with the actual file set (round 6), duplicate/contradictory issue-count
arithmetic (round 9), and the recurring stale-cross-reference class described above (rounds 7, 8,
14, 15). At the commit gate: confirmed no superseded phrasing survives in any form, confirmed
`_CURRENCY_SYMBOLS` and the SMI seed are genuinely untouched, confirmed `scope_paths` covers all
26 changed files, and flagged (non-blocking) that `.claude/active_work.md` is now ~95KB against
its own documented 32,000-byte injection cap.

VERDICT: PASS

## analytics-engineer-reviewer

PASS at rounds 11 through 16 after FAILs earlier in the cycle (stale currency-count arithmetic,
an incorrect "5 currencies" claim, sector-benchmark grouping questions). At the commit gate:
re-verified `int_stock__sector_benchmarks.sql` line-for-line against the Utilities/Industrials
narrative, re-ran the full pytest suite (391 passed) and all five CI gates rather than trusting
the prior round's run, and confirmed every forward-looking citation for the follow-up seed/base
contract resolves against live code.

VERDICT: PASS

## data-engineer-reviewer

PASS from round 9 onward, having FAILed rounds 1 through 8 on the constituent-cleaner mutation
gaps, the collision-guard blind spots, and the Block-ticker root cause. At the commit gate:
traced the sharpened Block mechanism (`ingest.py:213` writing the original ticker into the
fundamentals parquet, breaking `dim_stock`'s join key) line-by-line against source, confirmed
`docs/layering.md` never mentions seeds by grep, and confirmed no seed or ingestion file changed
since the prior review.

VERDICT: PASS

## cto-reviewer

PASS from round 11 onward after FAILing rounds 1 through 10 on guard mutation gaps and prose
drift. At the commit gate: confirmed the diff hash matches the staged tree, re-ran the full suite
(391 passed, exact collection count), confirmed both `_CURRENCY_SYMBOLS` copies are byte-identical
to before this branch, confirmed no seed was hand-corrected, and spot-checked ten file:line
citations against source (nine exact, one off-by-one on an untouched file, non-blocking).

VERDICT: PASS

## equity-analyst-reviewer

PASS from round 9 onward after FAILing earlier rounds on the currency-in-read-prompt scoping and
the Utilities/Industrials sector-count arithmetic. At the commit gate: recomputed the Utilities
7-without/8-with-Acciona-SA count directly from the `es_ibex35` seed rather than trusting the
prose, confirmed the "would unlock, not will" modal against the eligibility gate in
`int_stock__sector_benchmarks.sql`, and confirmed the CHF-in-read-prose finding stays escalated in
both the contract and the handover rather than silently resolved in code.

VERDICT: PASS
