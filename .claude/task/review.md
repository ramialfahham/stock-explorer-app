# Review

diff_sha256: 532974de4cc0c8c8f58d92883c7e06e5b2f163d78d3ec6bb100cd227fc8ccf1d

Five rounds. Reviewers: scope-auditor, cto-reviewer, analytics-engineer-reviewer and
equity-analyst-reviewer, all required by routing for the staged set. data-engineer-reviewer is
NOT required: no `supabase/*` file is staged.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role definition
verbatim first. Same role text, same cold blinded input, read-only.

**The verdict change itself was never the hard part.** It is one small function and two
conditions, and it measured clean from the first round: 32 cards move green to yellow, red
unchanged. Everything below is about what surrounded it.

**Three findings worth remembering.**

1. **The prompt told the model the opposite of what the verdict does.** `READ_SYSTEM_PROMPT`
   said growth is "context only, not a health signal". The bite was not staleness: the cards
   this change downgrades regenerate their prose, so each new paragraph would have been written
   under an instruction denying the reason for its own downgrade. Found independently by all
   three reviewers in round 1.
2. **Fixing scattered date stamps with a blanket regex broke 13 places.** Two broke the dbt
   parse and were caught; eleven compiled fine and were not. Sweep damage that still compiles
   is the damage you have to go looking for. It also edited an already-applied migration, which
   the filename-keyed runner could never re-apply, so the repo would have described a database
   comment that differs from the live one. Reverted: applied migrations are immutable.
3. **A test stopped covering what it claimed to.** The growth assertion was rewritten to read
   the `READ_METRIC_BRIEF` constant rather than the built prompt message, so deleting the gloss
   from `build_read_messages` would have left the suite green. Restored to assert on the built
   message, and verified non-vacuous by removing the gloss and confirming the test fails.

**The process failure behind all of it, recorded because it is the durable lesson.** This
session left 58 dated annotations across 17 files, plus a changelog line inside the production
prompt. The owner rejected both. The mechanism: each review round flagged a stale sentence, the
fix stamped a date on it, and the next round verified the date was accurate. **Accuracy was the
only test ever applied, because the reviewer briefs only ever asked "is this true" and never
"should this exist".** No reviewer role in this plugin owns repo cleanliness. Reviewer briefs
from here must ask about noise as well as correctness; this round's brief did, and that is how
the sweep damage was found.

**Open and escalated to the owner, NOT resolved here:** the growth metric's card copy says "One
quarter can be noisy, so look for a pattern over time" and renders on the same card types the
new gate downgrades, so a reader on one of the 32 cards sees a badge that moved on one quarter
and, one click away, text saying one quarter is noisy. Its base-effect caveats also cover only
the upside, while the downside is now the actionable half. §6 metric copy: the owner rewrites it.

## scope-auditor
VERDICT: PASS
risks_checked:
- All 19 staged paths inside `scope_paths`; the reverted migration correctly absent.
- `done_when`'s reviewer list matches `review_routing.json` against the actual staged files.
- No surviving prose anywhere asserts the verdict excludes growth.
- Every §6 item recorded with owner attribution: the 0% threshold, the prompt rewording, the
  `INPUT_HASH_VERSION` bump and its cost, the 32-card verdict change, burn staying unread.
- Final line-by-line pass for sweep damage after three earlier passes each missed sites.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `_is_shrinking` is null-safe and appears only in the green branches, so red is structurally
  unchanged; a randomised probe over boundary and non-finite values produced only green to
  yellow transitions.
- The growth assertion now covers the built prompt, proven by reconstructing the facts block
  without the gloss.
- `INPUT_HASH_VERSION` 5a.3 traced end to end: version is inside the hashed payload, so every
  card regenerates rather than the 32 whose colour moved.
- Applied-migration immutability: `013_net_cash.sql` byte-identical to main, exception recorded
  with its mechanism so a future sweep does not redo it.
- No new dependency, CI step, hook, permission or secret.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Proved the dbt edits are prose-only by parsing both schema files with descriptions masked:
  columns, data_tests and unit_tests are structurally identical.
- Both `.sql` files byte-identical after stripping comments.
- No column description left empty or damaged; the docs gate cannot newly fail.
- The verdict is not a warehouse concept, so no dbt prose can go stale against it.
- The null-growth path is consistent with the dbt eligibility contract.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- The prompt now states the app's rule rather than a categorical claim about revenue, which
  matters because the model has one quarterly figure and cannot tell a decline from a
  divestment, an FX move or contract timing.
- The growth gloss carries the financial-company caveat, matching the repo's existing wording
  for `net_margin_pct`.
- `docs/data_contract.md` carries the bank caveat: net interest plus fees moves with the rate
  cycle, and a bank shrinking a loan book can improve resilience while revenue falls.
- One-sidedness verified arithmetically: flat is not a decline, null is not a decline, and
  growth cannot reach red.
- The anti-advice guard survives the rewrite.
- The catalogue-copy contradiction is escalated, not rewritten, and recorded accurately
  including that the seed was in scope and left alone by choice.
