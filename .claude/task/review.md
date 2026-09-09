# Review

diff_sha256: 292e272eab8e97aa4bc180ddbdafad1640883c35ace8bdbb69f0b4dc6ca94a70

Four reviewers: scope-auditor (`always`), analytics-engineer-reviewer (`*.sql`),
data-engineer-reviewer (`supabase/*`), cto-reviewer (dispatched voluntarily, since
`.claude/working-agreement.md` has no required reviewer and governs every agent action here).
Four rounds. Written short on purpose: this branch exists to stop review records becoming
narrative.

## What shipped

`.claude/working-agreement.md` §2 gains the rule: prose earns its place only if it records a
decision not derivable from code, defines something the code cannot state, or is
machine-checked. Narrative goes to the commit message and MR description, with an explicit
carve-out that decisions and open items stay in `.claude/active_work.md`, which is injected into
the next session. Plus: when you change a claim, grep for the claim, not the file you were told
about.

Two instructions in that file were false and are corrected. Step 1 of the review cycle said
"Stage everything (`git add`)", which swept a 900 KB virtualenv into the index during MR !115;
it now requires explicit paths. §3 told agents to `git push origin <branch>` and use `gh pr`,
naming a remote that no longer exists in this clone; it now requires
`git push gitlab <branch>:<branch>` and `glab`, and states the `push.default = upstream` trap.

§3 also stopped overselling a guard. It claimed "a merge command" is hook-enforced;
`branch_discipline.py`'s `_GH_PR_MERGE` matches `gh pr merge` and nothing else, so
`glab mr merge` is unguarded. It now says so.

`.claude/task/contract.md` is rewritten with no `amendments:` section, 35,527 bytes to 3,301.
`.claude/active_work.md` drops four dated narrative sections, 31,980 bytes to 27,780 against a
32,000-byte cap it was 20 bytes under.

Facts that were load-bearing but lived only in the deleted narrative moved next to what they
describe: export timing, the `statement_timeout` uncertainty and the PostgREST schema cache to
`docs/supabase_setup.md` §3c; the column-list rationale into the migration; the owner-approved
15-60 minute band for `_DECK_TTL_SECONDS` into a comment beside that constant.

The dead `origin` remote was deleted from the clone. Not in the diff, but it is why §3 changed.

## Verification

`pytest tests/ -q` 615 passed. No executable line changed anywhere: both non-markdown files are
comment-only, verified line by line by three reviewers independently. Zero em-dashes and zero
lines over 100 characters across 234 added lines. `sqlfluff` is deliberately NOT cited: it lints
`dbt_analytics/models` and `dbt_analytics/tests` only and cannot see the migration whose comment
changed, so claiming it would manufacture coverage this diff does not have.

## The recurring author error

Relocating a claim without re-verifying it in its new context. The "80-column" count and the
REST-reachability reason were both true where they came from and false where they landed. Four
rounds found seventeen defects, all prose.

## scope-auditor

Failed rounds 1 and 2. Found five over-deletions, one with no other home in the repo (the open
finding that the AI read and the card face disagree on labels and units), a false forwarding
pointer to an archive that predates the MRs it named, and an owner-approved parameter band that
existed nowhere else. Then found the standing decision rewritten in this commit contradicted two
self-histories left standing in the same file.

VERDICT: PASS

## analytics-engineer-reviewer

Failed rounds 2 and 3. Found `done_when` citing `sqlfluff` as evidence for a file `sqlfluff`
cannot lint, three rules stated twice across the handover and the working agreement, and the
inverted changelog rule that contradicted the `## Recently merged` section this commit added.
Confirmed the migration comment's copy count and which copy is machine-checked, independently.

VERDICT: PASS

## data-engineer-reviewer

Failed round 2 on the migration comment's "80-column" figure, established the real numbers by
counting (78 payload keys, not 80), and recommended deleting the count rather than correcting it
since a count in a comment rots on the next `add column`. Then found `docs/supabase_setup.md`
giving a checkably false reason for the `statement_timeout` question being open.

VERDICT: PASS

## cto-reviewer

Failed round 2 on the one finding that made the repo less safe than before this branch: §3
generalised "`gh pr merge` is hook-blocked" into "a merge command", which is false and pointed
agents at the unguarded path. Supplied the stopping rule and the judgement that rounds 3 and 4
were past the point of return.

VERDICT: PASS

## Owner decisions

Three `NOT DONE, FLAGGED` entries in `contract.md`, none decided here:

- `CONTRACT_TEMPLATE.md` and `REVIEW_TEMPLATE.md` live in the dbt-agent-kit plugin and still
  prescribe the categories removed here. Editing them changes every project using the plugin.
- The merge guard covers `gh pr merge` only. Closing it means editing
  `~/.claude/hooks/branch_discipline.py`, a per-machine file every project shares.
- `.claude/working-agreement.md` has no required reviewer in `review_routing.json` beyond
  `always`. cto-reviewer recommends adding it, on the grounds that routing already sends
  `.claude/settings.json` and `*hooks/*` there for carrying execution authority, and this file
  carries instruction authority. The evidence is this branch: the one blocking correctness
  finding came from the reviewer routing did not require.

## Follow-ups, disclosed not fixed

- `.claude/active_work.md` quotes `"no such remote"` as the failure of a bare `git push origin`.
  cto and data-engineer each corrected it differently (the actual message is
  `fatal: 'origin' does not appear to be a git repository`, and `push.default = upstream` may
  error first). The substance is right and is the whole deterrent. Delete the quoted string
  rather than correct it a third time.
- Three date-stamped fixes remain in `.claude/active_work.md`, which its own standing decision
  forbids. All pre-existing and equally in conflict before this branch.
- The `!95-!98` entry in `## Recently merged` frames process rather than state. Inside the
  reconciling reading, but the one entry that strains it.
- `docs/handover_2026-09-03.md` carries the SUPERSEDED wording of this same rule ("git, this
  file, the contract and the review record carry the history"). It is a dated archive, framed as
  one, and outside `scope_paths`; editing it to agree with the present would destroy the
  property that makes an archive worth keeping. But a session grepping for the rule hits both
  wordings with nothing marking one superseded. Whether an archive may carry a "superseded by"
  annotation is a rule question about how archives work here, so it is the owner's.
- cto's stopping judgement, recorded because the next person to run this cycle should weigh it:
  routing is path-keyed, so a docs-only branch pulls the same full panel a data-model change
  does. Rounds 1 and 2 did the real work here; rounds 3 and 4 produced one contradiction and one
  misquoted git message.
