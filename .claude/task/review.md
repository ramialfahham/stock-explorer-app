# Review

diff_sha256: 054e24f64c0130bede309126e81eac6c48a2f3114ae5466a4604a22f18baf310
rounds: 3

Issue #47, MR 2 of 2. Round 1 (tree 4b70411): equity-analyst-reviewer FAIL (the identity key was the bare card ticker, which merges unrelated companies), platform-reviewer FAIL (one test did not discriminate), scope-auditor ESCALATE (saved identity; a stale-sentence file outside scope). Round 2 (tree 17da89d): equity-analyst-reviewer PASS, platform-reviewer FAIL (the dedupe-before-filter order had no test), scope-auditor ESCALATE (delegation record, dedupe order, FE-1). Round 3 (tree c693b6d, the cap): all three PASS. equity-analyst-reviewer ran as a general-purpose agent following `.claude/agents/equity-analyst-reviewer.md` verbatim on that role's model (#48).

Wording fixes applied after the round-3 PASS verdicts, no fourth round (the precedent in #46's review): the `active_work.md` FE-1 clause and the !248 state; the contract's statement of the user-visible changes (the 24 unrelated pairs show two cards again, five same-company pairs become two with News Corp's Class B pair precise, the Airbus and ArcelorMittal tie holds at equal snapshot_dates, the eligible-listings-only limit, the unmapped-market limit); the `dedupe_by_company` name in data_contract.md step 10 so the FE-1 exception is findable; the "(one per index)" gloss in north_star.md. Follow-ups filed as #58.

After the PASS verdicts the branch was rebased onto main with !248 merged (7c4aace). The patch text changed with its context lines, so the diff hash above is the post-rebase one, and two data_contract.md sentences were shortened (the peer-threshold line !248 had lengthened, and a path in step 10) to meet that file's byte budget, which !248 plus this MR together exceeded by 75 bytes. No code changed.

Coordinator evidence: six mutations, each caught by a new test (bare ticker as identity, saved check by listing only, tie-break removed, dedupe after the filters, sector options not deduped, dedupe put back in `fetch_deck`); the four tests of round 1 fail on main; full suite 1161 passed; `scripts/bootstrap.py --verify` passes; the em-dash check passes; the contract greps return nothing.

## Owner answers

CPO ANSWER: recorded for #47. (a) Delegation: the owner wrote in this session "I have no idea. You should act as the expert." and later "go"; every decision in the contract's decisions_reserved except the FE-1 exception was made by the agent under that delegation, each stated with its reason before "go". (b) Dedupe before the sector and preset filters, saved state per listing, and the tie to registry order: decided by the agent under that delegation. (c) FE-1 (deduplication in the display layer): asked of the owner directly, who answered "A": record the exception and keep the rule in the display layer. It is recorded as criteria version 2 in docs/quality_criteria.json with its fingerprint in tests/tooling/test_quality_audit.py.

## scope-auditor

VERDICT: PASS
reviewed_tree: c693b6dd935ed29155db7c6cc841331cdc641fd3
risks_checked:
- Every owner-level item in the delta (All-markets list contents, tie-break winner and sector label, sector options, per-company saved semantics, north_star Save wording, FE-1 exception) is in decisions_reserved under the delegation or answer A; none slipped in silently.
- The criteria bump changes only the version and the FE-1 rule text; version 1's fingerprint is untouched.
- Saved state and the single-market path are unchanged against main; fetch_deck matches done_when.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: c693b6dd935ed29155db7c6cc841331cdc641fd3
risks_checked:
- The round-2 FAIL is closed: both ordering tests fail under "dedupe after the filters"; the sector-options test fails if the All-markets dedupe is removed.
- `sectors_for_market` has one call site and its single-market path is unchanged.
- The suffix map equals the registry for all 15 markets and the test compares values.
wording_fixes: applied.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: c693b6dd935ed29155db7c6cc841331cdc641fd3
risks_checked:
- Deduping before the sector and preset filters is the financially safer order: the row that passes a filter is the row the card shows.
- The claim that the winner's market decides whether the sector comparison shows is true and disclosed in three places.
- No metric, label, interpretation or verdict wording changed; no advice language.
wording_fixes: applied.
