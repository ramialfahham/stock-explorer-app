# Review

diff_sha256: a7f4aa4fc5f2d60c5cd8099023bba941ecc696564edc517c9ba29c3b2224b451

Two review rounds. Required reviewer per routing (`.claude/review_routing.json`): scope-auditor
(always). No other pattern in the routing matches this file set (a new `docs/backlog/*.md` file
plus `.claude/active_work.md` and `.claude/task/contract.md`), so no other reviewer is required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so scope-auditor ran as a general-purpose agent instructed to read its own role
file verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file
and sha256 before every dispatch and never moved while the reviewer was running.

**Final verdict (round 2, the commit gate):** scope-auditor PASS.

## What this is

Scopes the name-vs-yfinance audit-guard mechanism as its own backlog item, per the owner's
request. This was flagged three times during this session's Nikkei, SMI, and Block ticker fixes
but never built, each time correctly deferred as a separable, owner-decided mechanism rather than
folded into the data fix at hand. Adds `docs/backlog/name_vs_yfinance_audit_guard.md`, matching
the shape of the one existing backlog doc, and links `.claude/active_work.md`'s existing mention
of the idea to it instead of leaving it as bare prose with no pointer. Documentation only: no
code, no CI, no new dependency.

## Round-by-round findings and fixes

**Round 1**: passed, with one non-blocking accuracy note: the doc's "Scope" open question
compared `docs/constituent_sources.yml`'s `provider:` field against the raw seed CSV's own
per-row `source` column as if they were opposites of the same axis, when they are two different
fields. Fixed: reworded to compare `provider:` consistently on both sides (`jp_nikkei225` is
`provider: manual`, verified against the actual file).

**Round 2**: passed clean, with the fix independently re-verified against the real
`docs/constituent_sources.yml`, and a byte-diff of the two frozen patches confirming nothing else
changed between rounds.

## scope-auditor
VERDICT: PASS
risks_checked:
- The cited numbers (2 of 11 Nikkei defects caught by the existing collision guard, 9 missed;
  nineteen SMI names) were cross-checked against the actual test file and prior session prose,
  not invented or rounded.
- `docs/north_star.md`'s "Phase 2 backlog" table was correctly left untouched: it is
  product-engagement backlog, a different category from this data-quality/CI item, confirmed by
  reading the table's own rows rather than assumed.
- No decision was silently made inside the "draft acceptance criteria" or "open questions"
  sections: every open question (live-fetch vs. cached, fuzzy tolerance, scope, failure mode,
  new-mechanism sign-off) is left genuinely unanswered, deferred to the owner.
- No em/en dash on any added line, across both rounds.
- No code, CI, or dependency file touched anywhere in the diff: scoping prose only.
