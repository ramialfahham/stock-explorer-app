# Review

diff_sha256: 88b7199831bc882cdb4736b96893e3579f40effc1faee1a2a15c64b56393ab63

Two review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), analytics-engineer-reviewer (`*.csv`), cto-reviewer (`tests/*`),
data-engineer-reviewer (`ingestion/*`). equity-analyst-reviewer is not routed to this diff's
file set.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 2, the commit gate):** scope-auditor PASS, analytics-engineer-reviewer
PASS, cto-reviewer PASS, data-engineer-reviewer PASS.

## What this is

Fixes `au_asx200`'s wrong Block ticker (seed says `XYX`, real ASX symbol is `XYZ`; `XYX.AX` and
`SQ2.AX` both 404 on Yahoo, `XYZ.AX` resolves to Block, Inc. in AUD). Root cause: Wikipedia's own
live S&P/ASX 200 table still lists `XYX` today, confirmed by fetching it with the repo's own
`_fetch_wikipedia_table`, so this is not a scraper bug and a raw-seed hand-edit would get
silently reverted the next time `scripts/refresh_constituents.py` runs for this market.

Unlike the prior Nikkei/SMI name fixes, this can't be a dbt-layer override: `ingestion/yfinance/
ingest.py` builds the yfinance fetch list from the raw seed before dbt ever runs, so a wrong
ticker means zero data fetched, not a display defect. Built a new ingestion-time override
instead: `ingestion/constituents/ticker_overrides.csv` (one row today), applied inside
`ingestion/constituents/seeds.py`'s `load_constituents()` via a new pure `_apply_ticker_overrides`
function, which is the single choke point all four current callers already go through. The raw
seed stays untouched, matching Wikipedia, exactly as designed. Owner-authorized 2026-08-29
("proceed with 1-5") after the root cause and design tradeoff were presented.

## Round-by-round findings and fixes

**Round 1**: three reviewers passed clean (scope-auditor, analytics-engineer-reviewer,
data-engineer-reviewer, the last confirming the interception point reaches every caller
correctly). cto-reviewer failed on a real defect found by empirical reproduction, not just
reading: `_load_ticker_overrides()` had no schema validation, so a genuinely empty (zero-byte)
override file raised `pandas.errors.EmptyDataError`, and a file with renamed columns raised a
bare `KeyError` deep inside `_apply_ticker_overrides`, both propagating for every market, not
just the one with an override, directly contradicting the contract's own "empty or missing file
is a no-op" claim. Also flagged a cosmetic inaccuracy: a comment claimed certain allowlist
entries were "below" a given one when some were actually above it. Both fixed: `_load_ticker_
overrides()` now mirrors `load_constituents()`'s own missing-columns check, with an
`EmptyDataError` catch for the zero-byte case; three new tests pin both no-op cases and the
loud-failure case; the comment reworded to be direction-neutral.

**Round 2**: all four required reviewers passed clean on a fresh, cold, independent pass. Three
mutation-tested or empirically reproduced the round-1 crash modes against the fixed code (not
just reading the diff) to confirm the fix is genuine. data-engineer-reviewer raised, then
accepted as an intentional and tested tradeoff, that treating a missing override file the same
as an empty one is a narrow blind spot against accidental file deletion, mitigated by the
end-to-end test running against the real on-disk files, which would catch exactly that in CI.
No further findings.

## scope-auditor
VERDICT: PASS
risks_checked:
- Raw seed CSV (`storage/seeds/au_asx200/constituents.csv`) confirmed untouched and still reads
  `XYX`; the correction lives entirely in the new override file, matching `decisions_reserved`.
- Every changed file falls inside `scope_paths`; no `dbt_analytics/` path touched anywhere.
- Both round-1 crash modes reproduced independently against the fixed code and confirmed gone.
- No em/en dash on any added line (scanned as both decoded text and raw UTF-8 bytes).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No dbt model, seed, or schema content anywhere in this diff; `dbt_project.yml`'s
  `seed-paths: ["seeds"]` also confirms the new CSV can never be picked up as a dbt seed.
- The three round-1 regression tests pass, and `dbt build --full-refresh` plus all five CI
  gate scripts stay green with the new ingestion-layer files present.
- Downstream reach independently verified: exactly the four claimed callers of
  `load_constituents()`, none modified, confirming the fix propagates everywhere it should.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Reconstructed the pre-fix code in-memory and confirmed it reproduces both original crash
  modes exactly, then confirmed the actual fix eliminates both, proving the fix is real and
  the new tests are not vacuous.
- Confirmed the `monkeypatch.setattr(seeds, "TICKER_OVERRIDES_PATH", ...)` pattern in the new
  tests actually targets the binding `_load_ticker_overrides()` reads, not a dead copy.
- No new dependency, no CI/hook change, no cost change; the override read is a stateless,
  idempotent CSV read added to an existing function.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Re-verified all four round-1 findings still hold against the current diff: interception
  completeness, column isolation, raw-seed non-mutation, and exchange-suffix composition order.
- Missing-vs-empty-file equivalence as a potential operational blind spot: accepted as an
  intentional, contract-authorized, and tested tradeoff, since the end-to-end test against the
  real on-disk files would catch an accidentally deleted or corrupted override file in CI.
- Confirmed the new defensive-read pattern is correctly scoped to `_load_ticker_overrides()`
  alone and should not be extended to the raw-seed loader, which is correctly fail-loud instead.
