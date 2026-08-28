# Review

diff_sha256: 643af1d9186b19078319b4db8a5072e0376fcae6aa1c88ec114f77facc5b6576

Two review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), analytics-engineer-reviewer (`*.csv`), cto-reviewer (`tests/*`).
data-engineer-reviewer and equity-analyst-reviewer are not routed to this diff's file set.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 2, the commit gate):** scope-auditor PASS, analytics-engineer-reviewer
PASS, cto-reviewer PASS.

## What this is

Fixes the SMI legal-name register by adding nineteen `ch_smi` rows to the existing
`company_name_overrides` seed (built for the prior merged Nikkei fix, mechanism unchanged): the
Swiss constituent source gives legal names ("Novartis International AG") where every other
market gives trade names ("Adidas"), and two of the nineteen (NOVN, SREN) were also factually
wrong, not just formal. Names were proposed by comparing the seed against yfinance `longName`,
presented to the owner as a full table, and approved verbatim. `KNIN` is excluded: its seed name
is already a trade name. Adds a pinning test mirroring the Nikkei one; no dbt model, schema, or
SQL change, since the override mechanism already generalizes across markets.

## Round-by-round findings and fixes

**Round 1**: scope-auditor failed on a real miss: `.claude/active_work.md` is listed in
`scope_paths` but was not actually edited, so its SMI section still said the name list "still
wants an owner's eye," directly contradicting this task's own `decisions_reserved` (the list was
already approved). analytics-engineer-reviewer independently flagged the same staleness as a
non-blocking observation. cto-reviewer passed but flagged two cleanups: a dead assertion
(`assert "KNIN" not in covered`) in the new test that was logically subsumed by the preceding
set-equality check and could never fail on its own, and the `HOLN` row's `reason` text using a
"yfinance lists the issuer as X" framing inconsistent with the contract's stated 2-wrong/
17-register-only split. All three fixed: the handover section rewritten to state the fix is done
and the name list was approved; the dead assertion removed (mutation-tested afterward: dropping
a ticker or adding a spurious one both correctly fail the remaining assertion); `HOLN`'s reason
reworded to match the other sixteen register-only rows.

**Round 2**: all three required reviewers passed clean on a fresh, cold, independent pass, with
explicit re-verification of every round-1 fix (including live mutation-testing the strengthened
test) rather than trusting it was done correctly. No further findings.

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-1 handover staleness is genuinely fixed, not just patched over: grepped the whole
  repo for the stale phrasing to rule out an orphaned copy elsewhere.
- Every changed file falls inside `scope_paths`; the raw seed CSV is untouched.
- `KNIN` correctly excluded; all nineteen tickers and their reason-column classification
  (2 factually wrong, 17 register-only) match the contract's done_when exactly.
- No em/en dash on any added line (byte-scanned every `+` line in the frozen patch).
- No new mechanism: `_seeds.yml`, `_manual_staging.yml`, `_yfinance_base.yml`, and
  `base_yf__constituents.sql` are all confirmed untouched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Join fan-out from a duplicate override key: confirmed zero duplicate `(market_code, ticker)`
  pairs across all 30 seed rows, and confirmed the join is a left join with a coalesce, not one
  that could fan out rows even if duplicates existed.
- Mapping correctness: read the raw `storage/seeds/ch_smi/constituents.csv` directly and
  confirmed all nineteen override tickers exist there, so no override row silently applies
  nothing against a renumbered or removed ticker.
- Full pipeline green: `dbt build --full-refresh` (122/122), `dbt docs generate` +
  `check_dbt_documentation.py`, all five gate scripts, `pytest` (395 passed).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Test mutation safety: rather than trusting the fix, mutated the seed two ways (dropped a
  ticker, added a spurious one) and confirmed the new test's single remaining assertion catches
  both, so it is not vacuous.
- Re-run/idempotency: `dbt build --full-refresh` is a clean seed-table replace with no
  incremental or stateful logic; no new mechanism introduced that could behave differently on a
  second run or a mid-run failure.
