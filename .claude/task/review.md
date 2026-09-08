# Review

diff_sha256: 371fa336f8fba3cdb3fd0c05177157211f4697d2848974fdd01fd9b9798451aa

## scope-auditor
Round 1 FAILED (two findings)
- `docs/data_contract.md` enumerates a closed set of reasons `ai_read` can be absent (a
  brand-new card, a per-card API failure, or a hallucination-guard reject) -- this diff adds a
  fourth (style-guard reject) to the exact same function without updating that enumeration, a
  real doc-sync gap the file wasn't in scope_paths to catch.
- `done_when`'s own em-dash-scan claim ("confirmed exactly these 5 hits... No accidental dash
  anywhere else in the diff") was itself false: a 6th, undisclosed em dash was sitting inside
  `contract.md` itself, in the sentence describing the earlier dash-corruption incident.

Also confirmed clean by this round: diff scope otherwise conformant; working-agreement.md §6
and active_work.md's open item 8 citations verified accurate; every rule
`find_read_style_violations` checks traced to real, verbatim `READ_SYSTEM_PROMPT` text; the
5-fixture-fix claim empirically correct; full suite 569/569. Two smaller, non-blocking accuracy
gaps also noted (a second undisclosed test using non-compliant placeholder text, harmless since
it's shielded by an earlier rejection; one comment whose justifying example doesn't quite
demonstrate what it claims) -- not fixed, correctly assessed as true nitpicks, not disclosure or
correctness problems.

Resolution: added a paragraph describing the new style guard to `docs/data_contract.md` right
before the enumeration, and added the fourth reason to the enumeration itself.
`docs/data_contract.md` added to scope_paths; equity-analyst-reviewer added to the required
review cycle. Reworded the sentence containing the undisclosed em dash to avoid needing the
character at all (rather than trying to "fix" it via escape sequences again -- see the note
below on why); independently re-verified via `hex(ord(ch))` against a standalone `.py` file,
0 hits now in that file, 5 hits total across the whole diff, all in the disclosed, legitimate
locations.

Note on how the 6th em dash slipped past a visual re-read during implementation: this session
separately confirmed that this machine's Bash tool output pipeline renders U+2014/U+2013 as the
Unicode replacement-character glyph even when the underlying file bytes are completely correct
(discovered when a `python -c` shell one-liner's `repr()` output showed `"�"` for a line
that was actually fine, nearly triggering an unnecessary "fix" that would have caused real
corruption). The reverse risk -- a real em dash rendering as if it were ordinary prose on a
visual read -- is what let this one through. Every dash-scan in this task from this point on
uses a standalone `.py` file (not a shell one-liner) and reports `hex(ord(ch))`, never the raw
character or `repr()` of a line containing it.

Round 2 (re-check of the two fixes only, nothing else in scope):
VERDICT: PASS
risks_checked:
- Doc-sync accuracy of the new style-guard paragraph and the 4-reason `ai_read`-absent
  enumeration -- verified line-by-line against the live `find_read_style_violations` function
  (all 10 individual checks map to the doc's prose) and against `generate_assessments.py`'s
  actual absence-producing control flow (brand-new / API failure / hallucination-guard reject /
  style-guard reject are 4 real, distinct paths), not just against the doc's own prose.
- Undisclosed em-dash/en-dash fully removed from `contract.md` -- verified with two independent
  programmatic scans (UTF-8 text-mode per-line, and a raw UTF-8 byte-sequence scan across the
  whole file), both from standalone `.py` files, neither piped through a command's stdin; both
  found zero.
- `scope_paths`/review-cycle citation accuracy -- cross-checked the claimed
  `review_routing.json:26` entry against the actual file content; exact match.
- No scope regression since round 1 -- `git status --porcelain`/`git diff --cached --stat` both
  confirm exactly the expected 7 staged files.

## cto-reviewer
Round 1 FAILED (three findings, all real regex false-positive bugs, each empirically confirmed
by the reviewer constructing and running an actual counter-example)
- `_NOT_JUST_RE`/`_BUT_WORD_RE`'s "but" search had no clause/sentence bound (searched from "not
  just" to the end of the whole string) -- misfired on a read using "not just X" in one sentence
  and an ordinary, unrelated contrastive "but" in a later one. Also directly contradicted
  scope-auditor round 1's incorrect assessment of the identical code ("the regex itself is
  correct, just the comment's illustration is imprecise" -- wrong).
- `_GROWTH_PERIOD_RE` matched "this year"/"over the year" anywhere in the read, not scoped to a
  growth statement -- broader than the prompt's actual rule. Misfired on a read discussing free
  cash flow, never growth.
- `_ADVICE_WORD_RE` matched "cheap"/"expensive"/"price"/"worth it" as bare words with no
  share/stock anchoring, unlike the adjacent, deliberately-anchored hold/avoid pattern --
  misfired rejecting a legitimate leverage/debt-cost explanation ("expensive to service").

Process note, disclosed by the reviewer itself: mid-review, it initially mistook a concurrent
`docs/data_contract.md` fix (scope-auditor's own resolution landing while cto-reviewer was still
running) for an unexplained mutation, reverted and unstaged it, then caught its own error by
cross-reading `review.md`, restored the edit, and re-staged it -- confirmed byte-identical to
the pre-revert state, both by the reviewer and independently on this end afterward. See
contract.md's amendments for the full account and the new `concurrent-agent-file-race` memory
this prompted.

Also confirmed clean by this round: wiring correctness; the `--dry-run` claim (verified directly
against `main()`); the 5 fixture edits are purely additive; the mutation-style wiring proof is
meaningful, not vacuous; emoji ranges/currency-symbol exclusion/verdict-ending limitation all
correct/adequately disclosed; no `.gitlab-ci.yml` change; no secrets; no new dependency; full
suite 569/569 (pre-fix count); em-dash scan clean (5 legitimate hits, independently re-verified
after scope-auditor's own fix).

Resolution, all three fixed together: combined "not just"/"but" into one sentence-bounded regex;
scoped the growth-period check to same-sentence proximity with a growth word, checked either
order; split the advice-word check into an unanchored group (buy/sell/price -- no legitimate
non-advice use) and merged cheap/expensive/worth-it into the same share/stock-anchored pattern
hold/avoid already used. New regression tests added for each (a same-sentence-vs-later-sentence
"but" pair, both growth-word/period-phrase orderings plus a not-about-growth clean case, a
combined anchored-value-word parametrized test, an expanded benign-use example directly reusing
the reviewer's own counter-example). Mutation-tested the "not just/but" fix specifically:
reverted the sentence bound, confirmed the new regression test fails with the exact predicted
symptom, restored, confirmed clean (573 passed, up from 569). Em-dash re-scanned after all three
fixes: still exactly 5 legitimate hits.

Round 2 (re-check of the three regex fixes only, nothing else in scope) FAILED (two findings,
both introduced by round-1's own fixes, both empirically confirmed with actual counter-examples)
- The growth-period per-sentence check's `re.split(r"[.!?]+", read)` also splits on the "."
  inside every percentage this app renders (`f"{v:.1f}%"`), so a real sentence with a figure
  between its growth word and period phrase gets cut into two fragments, neither containing
  both patterns -- violation silently missed. Named as the exact hazard the file's own comment
  already flags elsewhere (why "2-3 sentences" isn't checked), walked into anyway.
- The merged `_ADVICE_VALUE_SHARE_RE` doesn't distinguish "share" as the security from "share
  of X" (a portion -- on-topic, prompt-encouraged vocabulary per `READ_METRIC_BRIEF`'s own
  margin gloss) or "market share" (an unrelated business term). Confirmed with 5 constructions,
  all legitimate, all incorrectly rejected.

What held: `_NOT_JUST_BUT_RE`'s sentence bound -- stress-tested with semicolon/colon separators
and word-boundary collisions, held or unrealistic for Haiku's punctuated prose. Full suite
573/573 (pre-fix count, matches claim). Mutation test (fix 1 from round 1, per explicit request):
reverted the sentence bound via Edit, confirmed the regression test failed with the predicted
symptom, restored via Edit, verified narrowly scoped to `scripts/assessment_rules.py` only (per
the concurrent-edit-race lesson from this reviewer's own round 1). Em-dash scan: exactly 5 hits,
same legitimate locations, no 6th/undisclosed hit.

Resolution: while fixing finding 1, proactively checked whether the same root cause (naive `.`
as sentence boundary) also affected the two OTHER proximity-bounded checks sharing the identical
`[^.!?]`-based mechanism -- confirmed empirically, real bug in both, previously unreported.
Fixed as one root-cause change: a shared `_SENTENCE_GAP` pattern tolerating a decimal point
without treating it as a sentence end (used by `_NOT_JUST_BUT_RE` and `_ADVICE_VALUE_SHARE_RE`),
and a parallel `_SENTENCE_BOUNDARY_RE` split pattern with the identical decimal-tolerance logic
for the growth-period check. Finding 2 fixed with two lookaround exclusions (`(?<!market )`,
`(?!\s+of\b)`) on `_ADVICE_VALUE_SHARE_RE`, deliberately not extended to "stock" (no known,
demonstrated collision there -- not guessing at an unproven problem). 8 new regression tests
added, including the decimal-figure case for all three affected checks. Mutation-tested the
shared `_SENTENCE_GAP` fix: reverted to the bare character class, confirmed the two tests using
it failed with the predicted symptom while the independently-implemented growth-period test
correctly stayed green, restored, confirmed clean (581 passed, up from 573).

Round 3 (re-check of these two fixes only, nothing else in scope) FAILED (two more real bugs,
both introduced by round 2's own fix, both empirically demonstrated)
- `_SENTENCE_BOUNDARY_RE`'s decimal tolerance had inverted lookaround logic
  (`(?<!\d)\.(?!\d)`, an AND of negations, when the correct test is an OR): a whole-number-then-
  period ("...ratio of 1.50. This year..." / "...$400. This year...", both real shapes this
  app's own metric/money formatters produce) wrongly failed to split, merging two unrelated
  sentences into one fragment -- a FALSE POSITIVE on a compliant read. `_SENTENCE_GAP` (the
  sibling pattern from the same fix) got the equivalent logic right; only the independently-
  written split pattern had it backwards.
- `_ADVICE_VALUE_SHARE_RE`'s `(?<!market )`/`(?!\s+of\b)` exclusions sat outside the whole
  share/stock alternation, applying to all four words uniformly -- directly contradicting the
  adjacent comment's explicit claim and regressing round 1's correct behavior ("hold/avoid the
  stock of X" went from caught to silently missed). Contributing cause: zero test coverage of
  "stock" as the anchor noun anywhere in the test file -- this branch had never had a positive-
  catch test.

What held: the originally-reported round-2 bugs are genuinely fixed (8 regression tests pass;
`_SENTENCE_GAP` mutation-tested via Edit, confirmed correct). Full suite 581/581 before and
after. Em-dash scan: exactly 5 hits, same legitimate locations, no 6th/undisclosed hit.

Resolution: fixed the OR/AND inversion (alternation form,
`r"(?<!\d)\.|\.(?!\d)|[!?]+"`). Nested the share/stock exclusions inside the share/shares
branch specifically, so stock/stocks match unconditionally again. 7 new regression tests added
(4 parametrized hold/holding/avoid/avoiding-the-stock-of-X, one hold-market-stock, 2
parametrized whole-number-then-period cases using the reviewer's own exact counter-examples).
Mutation-tested the OR/AND fix: reverted to the inverted version, confirmed both parametrized
cases fail with the predicted symptom, restored, confirmed clean (588 passed, up from 581).

Round 4 (re-check of these two fixes only, nothing else in scope) -- genuinely adversarial
re-test given the 3-rounds-of-self-inflicted-bugs track record, not a rubber stamp:
VERDICT: PASS
risks_checked:
- `_SENTENCE_BOUNDARY_RE`'s OR-of-negations fix: 8 new adversarial cases (multiple whole
  numbers/decimals stacked back-to-back, a true violation landing after a whole-number split,
  growth-word/period-phrase correctly not bridged across an intervening whole-number sentence,
  no over-split of "24.0%"'s own internal decimal, whole numbers at both text edges, mixed
  `!`/`?` terminators) all held. Mutation-tested by reverting to the round-3 AND-bug via Edit: 3
  cases failed with exactly the predicted symptom, confirming real discriminating power;
  restored, byte-identical.
- `_ADVICE_VALUE_SHARE_RE`'s nested-branch fix: 8 new adversarial cases (uppercase "STOCK OF"
  still caught, uppercase/title-case "MARKET SHARE" still excluded, plural "shares of" also
  excluded, a branch-ordering/backtracking stress case, word-boundary stress against
  "stockpile"/"restock" substrings) all held. Mutation-tested by reverting to the round-2
  un-nested form: exactly the 2 cases targeting the leak failed with the predicted symptom,
  restored, byte-identical.
- The comment's claim that "stock" has no known share-of/market-share-style collision: checked
  empirically against this app's actual vocabulary (`metric_catalogue.csv`, `READ_SYSTEM_PROMPT`,
  `READ_METRIC_BRIEF`) rather than trusted -- only hits were "stockholders equity" (where `\b`
  after "stock" correctly fails to match) and the prompt's own "stock-learning app" self-
  description (instruction text, not something the LLM has cause to echo). No real collision
  found; round 3's claim stands.
- Full suite: 588/588, matching the claimed count, re-run again after mutation testing to rule
  out residual state.
- Em-dash scan: exactly 5 hits, same legitimate locations as every prior round, no 6th.
- Working-tree integrity: confirmed byte-identical to staged after this round's own Edit-based
  mutation testing -- no repeat of the round-1 concurrent-edit-race incident.

**All four required reviewers now PASS against the current, fully-staged diff**: scope-auditor
round 2, cto-reviewer round 4, equity-analyst-reviewer round 1.

## equity-analyst-reviewer
Round 1 (first look, required after scope-auditor round 1 added docs/data_contract.md to
scope):
VERDICT: PASS
risks_checked:
- Rule-category accuracy: every one of the 10 `violations.append()` call sites in
  `find_read_style_violations` cross-checked against the new doc paragraph's list and against
  `READ_SYSTEM_PROMPT`'s own near-verbatim wording -- every listed category real and traceable,
  nothing invented, nothing omitted. The doc's own "checks a subset... without semantic
  judgment" hedge matches the code docstring's disclosed partial-subset framing almost word for
  word -- no overclaim of completeness.
- Fail-closed/ordering claim verified directly against `_generate_read`: the style check runs
  immediately after the metric guard, identical `return None, None` path, identical
  self-healing consumption downstream.
- 4-reason enumeration traced against every `return None, None` in `_generate_read` -- accurate
  and complete for what this diff changes.
- ASCII-dash convention: independently re-scanned (standalone script, explicit UTF-8,
  `hex(ord(ch))` reporting only) both the new paragraph specifically and the full diff's added
  lines -- zero hits in the new prose, exactly 5 hits total diff-wide, all in the disclosed,
  legitimate locations, independently reproduced rather than trusted.
- Register/voice: new paragraph matches the surrounding ~150 lines' established dense,
  identifier-heavy technical style, including deliberately echoing the immediately preceding
  paragraph's own sentence construction.

Two non-blocking observations, not fixed (correctly assessed as true nitpicks, matching this
task's established bar for what rises to a finding): the guard function's home file
(`scripts/assessment_rules.py`) isn't named directly in this section's cross-reference ("same
file" -- accurate but requires the reader to trace it, low severity given the audience); the
doc groups exclamation-marks and emoji into one prose clause where done_when lists them
separately (cosmetic only, both remain independently-checked code paths either way).
