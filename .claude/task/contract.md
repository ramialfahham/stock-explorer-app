# Task contract

objective: Add a deterministic (non-LLM) style/rule guard for AI-generated card reads --
  `find_read_style_violations()` in `scripts/assessment_rules.py`, checking a subset of
  `READ_SYSTEM_PROMPT`'s own stated rules that a plain string/regex check can enforce without
  semantic judgment. Wired into `scripts/generate_assessments.py`'s `_generate_read`, alongside
  the existing hallucination guard (`validate_read_metrics`), same fail-closed treatment.

  Loosely "item 5" of an earlier, now-lost 5-item portfolio-readiness list -- my own bare
  one-line summary ("a periodic AI-output-quality eval") is the only trace of it anywhere; two
  prior tasks in this same loose sequence already showed a remembered number/description from
  that list can be wrong or unverifiable. Investigated what that summary could concretely mean:
  no fuller description exists anywhere in the repo or its git history (confirmed via targeted
  `git log --all -S` searches for "golden", "hallucination", "periodic AI", "AI-output-quality",
  "golden set", "ground truth", "LLM-judge" -- nothing beyond the summary). This repo's Claude
  API usage has zero cost governance today (no cap, no spend log -- already flagged, unaddressed,
  in `.claude/active_work.md`'s own open item 8), and a real periodic/scheduled sampling eval
  would add new recurring Claude spend and new CI/schedule infrastructure on top of that already-
  flagged problem -- a new mechanism plus a cost/schedule decision, both squarely
  `.claude/working-agreement.md` §6 (owner-only). Put to the owner directly (via `AskUserQuestion`,
  then confirmed again after an initial answer was dismissed): chose the cheaper, lower-regret
  shape -- extend the existing generation-time guard, zero new Claude spend, zero new
  infrastructure, same established fail-closed pattern already in place and already reviewed.

  Full technical design (exact regex patterns, false-positive reasoning for each rule, the
  em-dash in-memory-vs-file-scan distinction, the dry-run analysis) verified against source and
  approved via `ExitPlanMode`: `C:\Users\Rami\.claude\plans\groovy-churning-scroll.md`.

scope_paths:
  - scripts/assessment_rules.py (new find_read_style_violations function)
  - scripts/generate_assessments.py (wiring into _generate_read)
  - tests/tooling/test_assessment_rules.py (new test section)
  - tests/tooling/test_generate_assessments.py (fixture updates + new wiring tests)
  - docs/data_contract.md (scope-auditor round-1 doc-sync finding: the ai_read-absent
    enumeration needed a 4th reason added -- see amendments)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding -- the cost/mechanism decision (build this at all, and in
  this cheaper shape rather than a periodic LLM-judge) was put to the owner directly before any
  implementation, per §6. Remaining choices are implementation-level, disclosed as
  agent-executable, not product content: (1) which 6 of `READ_SYSTEM_PROMPT`'s rules are
  checkable deterministically (see plan's "Deliberately excluded" list for the ones left out and
  why -- a technical tractability judgment, not a product/wording call); (2) exact regex
  patterns and false-positive mitigations (word-boundary anchoring, hold/avoid scoped to
  share/stock, emoji ranges excluding currency symbols) -- engineering precision choices with
  documented reasoning, not new user-facing behavior (the prompt's rules are unchanged; this
  only adds enforcement of a subset already agreed and shipped).

done_when:
  - `find_read_style_violations(read: str) -> list[str]` exists in `scripts/assessment_rules.py`,
    checking: em/en-dash, exclamation marks, emoji, investment-advice language (buy/sell/cheap/
    expensive/worth it/price, hold/avoid anchored to share/stock), the prompt's own named AI-tell
    phrases ("not just X, but Y", "it's worth noting", "it's important to remember"), "this
    year"/"over the year" about growth, and ending on the verdict's meaning ("on these
    figures"/"on these numbers").
  - Wired into `_generate_read` (`scripts/generate_assessments.py`) immediately after the
    existing `validate_read_metrics` check, same fail-closed `return None, None`, stderr message
    naming every violated rule.
  - `--dry-run` unaffected (confirmed: returns before `_generate_read` is ever reachable, so
    inherits the existing guard's exemption for the identical reason -- no code change needed
    there, verified not assumed).
  - Five existing tests in `tests/tooling/test_generate_assessments.py` whose placeholder
    fixture text doesn't end with a verdict-meaning phrase updated to real closing text
    (mechanical fixture fix, not a design change) -- confirmed exactly which five by reading the
    file directly before implementing, not guessed.
  - New tests in `tests/tooling/test_assessment_rules.py`: one violating + one clean example per
    rule (the clean side proves precision, not just presence), plus the specific false-positive
    cases the design is built to avoid (ordinary hyphens, currency symbols/degree sign, sales/
    seller, "holds cash"/"avoid a cash squeeze", "not just X" without a later "but", both figures/
    numbers endings), plus a multi-violation read asserting every violation is reported.
  - New tests in `tests/tooling/test_generate_assessments.py`: style-violating read rejected
    (fails closed, correct stderr), style-clean read accepted, and a mutation-style wiring proof
    (monkeypatch the check to always pass, confirm a violating read now succeeds -- proving the
    call site actually depends on the real check, matching this file's own existing
    `test_operating_statement_roe_call_site_is_actually_wired` pattern).
  - `pytest tests/tooling/... -v` then full `pytest tests/ -q`: all green, no regressions.
  - Manual mutation check: comment out the new `if style_violations:` block, confirm the
    rejection test fails with the expected symptom, restore, confirm green again.
  - No em/en-dash on any added line OUTSIDE the 5 deliberate exceptions this task's own subject
    matter requires: the `_EM_DASH`/`_EN_DASH` constants in `find_read_style_violations` itself
    (a dash detector must hold the literal characters it detects, the same way a banned-words
    list must contain the banned words) and 3 test fixture strings constructing a read that
    actually contains one, to prove the detector catches it. Scanned (file-based UTF-8-explicit,
    not stdin) and confirmed exactly these 5 hits, each independently byte-verified via
    `hex(ord(ch))` against a standalone script (not a shell one-liner -- an earlier attempt to
    switch these to Unicode escape-sequence form via a `python -c` shell round-trip actually
    corrupted the file into literal U+FFFD replacement characters, caught immediately by a
    follow-up `hex(ord())` check before it was ever staged; reverted via Edit, re-verified
    clean).
  - Review cycle: scope-auditor + cto-reviewer + equity-analyst-reviewer. Originally scoped as
    scope-auditor + cto-reviewer only (no dbt/ingestion/frontend/data_contract files touched at
    the time) -- scope-auditor's own round-1 finding added `docs/data_contract.md` to
    scope_paths, which `.claude/review_routing.json` routes to equity-analyst-reviewer; added
    once discovered, not assumed away.

impact_map:
  - No user-visible change to the app itself. Changes which already-generated reads pass the
    existing accept/reject gate -- a read that violates one of these 6 rules now gets rejected
    (falls back to the existing deterministic `VERDICT_FALLBACK_READ` line) instead of being
    stored; a compliant read is unaffected either way.
  - `scripts/*` touched -> requires cto-reviewer per `.claude/review_routing.json`.
  - `docs/data_contract.md` touched -> requires equity-analyst-reviewer per
    `.claude/review_routing.json:26` (added after scope-auditor's round-1 finding; see
    scope_paths/amendments).
  - scope-auditor always.
  - No CI/schedule/dependency change -- confirmed no new job, no new Claude spend, no new
    infrastructure (the whole point of the chosen approach over the declined alternative).

amendments:
- scope-auditor (round 1) FAILED (two findings):
  1. `docs/data_contract.md` enumerates a closed set of reasons `ai_read` can be absent (a
     brand-new card, a per-card API failure, or a hallucination-guard reject) -- this diff adds
     a fourth (style-guard reject) to the exact same function without updating that
     enumeration, a real doc-sync gap the file wasn't in scope_paths to catch. Fixed: added a
     paragraph describing the new guard right before the enumeration, and added the fourth
     reason to the list itself. `docs/data_contract.md` added to scope_paths;
     equity-analyst-reviewer added to the required review cycle (see scope_paths/impact_map
     above).
  2. done_when's own em-dash-scan claim ("confirmed exactly these 5 hits... No accidental dash
     anywhere else in the diff") was itself false: a 6th, undisclosed em dash was sitting inside
     this same contract.md, in the sentence describing the earlier dash-corruption incident
     (ironic given the subject) -- a real, if minor, instance of the exact rule this task's own
     guard exists to help enforce. Fixed: reworded the sentence to avoid needing the character
     at all; independently re-verified via the same `hex(ord(ch))` byte-level method (not
     visual inspection, which is what let this slip through the first time -- the terminal's
     own rendering of these characters is unreliable, confirmed separately during
     implementation, see below) -- 0 hits now in this file.

  Also confirmed clean by scope-auditor round 1: diff scope otherwise conformant;
  working-agreement.md §6 and active_work.md's open item 8 citations verified accurate; every
  rule `find_read_style_violations` checks traced to real, verbatim `READ_SYSTEM_PROMPT` text;
  the 5-fixture-fix claim empirically correct; full suite 569/569.

  Two smaller, non-blocking accuracy gaps also noted, not fixed (correctly assessed as
  not independently FAIL-worthy, recorded for completeness): a second, undisclosed
  test using non-compliant placeholder text (`test_attach_reads_rejects_a_read_citing_a_number_
  that_does_not_match`, shielded from the style check by an earlier rejection, so harmless) and
  one comment (`assessment_rules.py`) whose justifying example doesn't actually demonstrate what
  it claims (`"about"` doesn't contain `"but"` as a substring either way -- the regex itself is
  correct, just the comment's illustration is imprecise). Left as-is: true nitpicks, not
  disclosure or correctness problems.

  Separate note on the terminal-rendering discovery, relevant to why the 6th em-dash wasn't
  caught by my own visual re-reads during implementation: this session independently confirmed
  that this machine's Bash tool output pipeline renders U+2014/U+2013 as the Unicode
  replacement-character glyph on the terminal even when the underlying file bytes are completely
  correct (verified via `hex(ord(ch))` against a standalone script, not a shell one-liner, after
  an earlier scare where the same rendering artifact was initially mistaken for real file
  corruption). The reverse risk -- a real em-dash rendering as if it were ordinary prose, easy to
  miss on a visual read -- is exactly what happened here. The file-based, explicit-UTF-8,
  `hex(ord())`-verified scan is the only fully reliable method on this machine; a visual
  re-read of prose, even carefully done, is not sufficient on its own going forward.

- **Process incident, mid-review**: while cto-reviewer's round 1 was still running (dispatched
  in parallel with scope-auditor against the same diff), scope-auditor's findings above were
  fixed and re-staged, including the `docs/data_contract.md` edit. cto-reviewer's own review
  process ran a git operation against the shared working tree that reverted that concurrent
  edit -- confirmed independently on this end too: `git status`/`git diff --cached` showed
  `docs/data_contract.md` completely absent (byte-identical to HEAD) partway through cto-
  reviewer's run, before it had finished. cto-reviewer caught this itself (cross-read
  `review.md`'s recorded resolution, restored the edit, re-staged, confirmed byte-identical to
  the pre-revert state) and disclosed it plainly in its own report. Independently re-verified
  the restoration afterward, matching cto-reviewer's account exactly. No content was lost;
  logged as a new memory (`concurrent-agent-file-race`) since this is a real, previously-
  undocumented risk class for this session's established pattern of dispatching reviewer agents
  with full write access into the same, non-isolated working tree.

- cto-reviewer (round 1) FAILED (three findings, all real regex false-positive bugs, each
  empirically confirmed by the reviewer constructing and running an actual counter-example, not
  just reasoned about):
  1. `_NOT_JUST_RE`/`_BUT_WORD_RE`'s "but" search had no clause/sentence bound (searched from
     "not just" to the end of the whole string) -- misfired on a read using "not just X" in one
     sentence and an ordinary, unrelated contrastive "but" in a later one (a yellow-verdict card
     contrasting a weak axis against a strong one is exactly this shape). Also directly
     contradicted this contract's own earlier, incorrect assessment of the identical code
     (scope-auditor round 1's "the regex itself is correct, just the comment's illustration is
     imprecise" -- wrong; there was a real functional bug independent of the comment).
  2. `_GROWTH_PERIOD_RE` matched "this year"/"over the year" anywhere in the read, not scoped to
     a growth statement -- broader than the prompt's actual rule ("do not write 'this
     year'... about it", where "it" = growth specifically). Misfired on a read discussing free
     cash flow, never growth.
  3. `_ADVICE_WORD_RE` matched "cheap"/"expensive"/"price"/"worth it" as bare words with no
     share/stock anchoring, unlike the adjacent, deliberately-anchored hold/avoid pattern --
     misfired rejecting a legitimate leverage/debt-cost explanation ("expensive to service").

  Each of these silently degrades a genuinely compliant card to the deterministic fallback line
  -- the highest-stakes failure mode for this guard, and (per cto-reviewer's own observation)
  indirectly increases repeat Claude API calls too, since a rejected read never gets stored and
  the card retries every future pipeline run -- undermining the "zero new Claude spend"
  rationale for choosing this approach over a periodic LLM-judge in the first place.

  Resolution, all three fixed together:
  1. Combined into one bounded regex, `_NOT_JUST_BUT_RE = r"\bnot just\b[^.!?]*\bbut\b"` -- "but"
     must now appear in the SAME sentence as "not just", not merely somewhere later in the text.
  2. Scoped to same-sentence proximity with a growth word (growth/grew/grown/growing), checked
     per-sentence (`re.split(r"[.!?]+", read)`) rather than a single directional regex, since the
     growth word can legitimately come before OR after the period phrase.
  3. Split the old `_ADVICE_WORD_RE` into `_ADVICE_ACTION_RE` (buy/sell/price -- kept bare-word,
     no legitimate non-advice use exists in this app's vocabulary) and merged cheap/expensive/
     worth-it into the SAME anchored pattern hold/avoid already used (now `_ADVICE_VALUE_SHARE_RE`),
     since all five share the identical false-positive risk and the identical fix.

  New regression tests added for each: a same-sentence-vs-later-sentence "but" pair, both
  orderings of the growth-word/period-phrase proximity plus a not-about-growth clean case, and a
  combined anchored-value-word parametrized test (merging the old separate hold/avoid test) plus
  an expanded benign-use clean example directly reusing cto-reviewer's own leverage-cost
  counter-example. All three fixes re-verified together: full suite re-run (573 passed, up from
  569), em-dash re-scanned (still exactly 5 legitimate hits, standalone-script method).

  Also confirmed clean by cto-reviewer round 1: wiring correctness (call order, fail-closed
  shape, stderr message completeness); the `--dry-run` claim (verified directly against
  `main()`); the 5 fixture edits are purely additive, each still asserting the same property it
  always did; the mutation-style wiring proof is meaningful, not vacuous; emoji ranges/currency-
  symbol exclusion/verdict-ending presence-not-suffix limitation all correct/adequately
  disclosed; no `.gitlab-ci.yml` change; no secrets; no new dependency (`re` is stdlib).

  Round 2 (re-check of the three regex fixes only, nothing else in scope) FAILED with two more
  real bugs, BOTH introduced by the round-1 fixes themselves, both empirically confirmed by
  cto-reviewer constructing and running actual counter-examples:
  1. The growth-period per-sentence check's `re.split(r"[.!?]+", read)` also splits on the "."
     inside every percentage this app renders (`f"{v:.1f}%"`, always one decimal) -- a real
     sentence with a figure sitting between its growth word and period phrase (e.g. "Revenue
     grew 24.0% this year") gets cut into two fragments, neither containing both patterns, so
     the violation is silently missed. The file's own comment elsewhere already names this exact
     hazard for why "2-3 sentences" was deliberately not checked -- walked into anyway here.
  2. The merged `_ADVICE_VALUE_SHARE_RE` doesn't distinguish "share" as the security from
     "share" as "a portion of X" -- on-topic, system-prompt-encouraged vocabulary
     (`READ_METRIC_BRIEF`'s own margin gloss literally says "share of sales kept as... operating
     profit"; the existing `_CLEAN_READ` fixture already uses "a solid share of every sale").
     "market share" is a separate, similarly legitimate collision. Confirmed with 5 constructions,
     all legitimate, all incorrectly rejected.

  What held (not re-broken): `_NOT_JUST_BUT_RE`'s sentence bound -- stress-tested with
  semicolon/colon separators and word-boundary collisions, all held or are unrealistic edge
  cases for Haiku's punctuated prose.

  While fixing finding 1, proactively checked whether the SAME root cause (naively treating any
  "." as a sentence boundary) also affected the two OTHER proximity-bounded checks that use an
  identical `[^.!?]`-based mechanism, rather than assuming the fix was isolated to the one
  reported instance. Confirmed empirically, real bug in both, previously unreported: a decimal
  figure sitting inside the `_NOT_JUST_BUT_RE`/`_ADVICE_VALUE_SHARE_RE` proximity window also
  silently defeats both checks, for the identical reason. Fixed as one root-cause change rather
  than three separate patches: a shared `_SENTENCE_GAP` pattern
  (`r"(?:[^.!?]|(?<=\d)\.(?=\d))"`) that tolerates a decimal point without treating it as a
  sentence end, used by both proximity-bounded regexes; a parallel `_SENTENCE_BOUNDARY_RE`
  (`r"(?<!\d)\.(?!\d)|[!?]+"`) for the growth-period check's `.split()`, with the identical
  decimal-tolerance logic expressed as a split pattern instead of an inline alternation.

  Finding 2 fixed with two lookaround exclusions on `_ADVICE_VALUE_SHARE_RE`: `(?<!market )`
  before the share/stock alternation (excludes "market share"), `(?!\s+of\b)` after it (excludes
  "share of X"). Deliberately NOT extended to "stock": no card metric describes inventory/
  stock-levels, so no equivalent collision is known to exist there, and adding an unproven
  exclusion would be guessing at a problem rather than fixing a confirmed one.

  8 new regression tests added (5 parametrized share-as-portion/market-share clean cases directly
  reusing cto-reviewer's own counter-examples, one decimal-figure case for each of the three
  affected checks). Mutation-tested the shared `_SENTENCE_GAP` fix specifically: reverted it to
  the pre-fix bare character class, confirmed the two regression tests using it fail with the
  exact predicted symptom while the growth-period test (a separate mechanism) correctly stayed
  green, restored, confirmed clean (581 passed, up from 573). Em-dash re-scanned after these
  fixes: still exactly 5 legitimate hits (standalone-script method).

  equity-analyst-reviewer (round 1, on the new `docs/data_contract.md` paragraph, first look)
  PASSED -- see review.md for the full risks-checked account.

  Round 3 (re-check of the two round-2 fixes only, nothing else in scope) FAILED with two MORE
  real bugs, both introduced by round 2's own fix, both empirically demonstrated:
  1. `_SENTENCE_BOUNDARY_RE`'s decimal-tolerance had inverted lookaround logic: `(?<!\d)\.(?!\d)`
     requires BOTH sides digit-free to count as a sentence end -- the correct test is an OR of
     the two negations, not an AND (a period is a decimal point only when BOTH sides are digits;
     it is a real sentence end whenever EITHER side is not a digit). The bug: a whole-number-
     then-period ("...ratio of 1.50. This year..." or "...$400. This year...", both real shapes
     this app's own metric/money formatters produce) wrongly failed to split, merging two
     unrelated sentences into one fragment -- a FALSE POSITIVE growth/"this year" violation on a
     compliant read. `_SENTENCE_GAP` (the sibling pattern from the same round-2 fix) got the
     equivalent logic right; only the independently-written split pattern had it backwards.
  2. `_ADVICE_VALUE_SHARE_RE`'s `(?<!market )`/`(?!\s+of\b)` exclusions sat OUTSIDE the
     `(?:share|shares|stock|stocks)` alternation, so they applied to all four words uniformly --
     directly contradicting the adjacent comment's explicit claim ("Neither exclusion touches
     'stock'") and regressing round 1's correct behavior ("hold/avoid the stock of X" went from
     caught to silently missed). Contributing cause: zero test coverage of "stock" as the anchor
     noun anywhere in the test file, including all 5 round-2 portion-language tests -- this
     branch had never had a positive-catch test, which is how the leak survived two rounds.

  What held: the originally-reported round-2 bugs are genuinely fixed (8 regression tests all
  pass; `_SENTENCE_GAP` itself mutation-tested via Edit, confirmed correct); full suite 581/581
  before and after; em-dash scan clean, 5 legitimate hits, no 6th.

  Resolution: fixed the OR/AND inversion (`_SENTENCE_BOUNDARY_RE = r"(?<!\d)\.|\.(?!\d)|[!?]+"`
  -- the alternation form of the OR, since a single lookaround can't express it directly).
  Nested the share/stock exclusions inside the share/shares branch specifically
  (`r"\b(?:(?<!market )(?:share|shares)\b(?!\s+of\b)|(?:stock|stocks)\b)"`), so "stock"/"stocks"
  match unconditionally again, matching the comment's own (now-true) claim. 7 new regression
  tests added: 4 parametrized hold/holding/avoid/avoiding-the-stock-of-X cases, one hold-market-
  stock case, and 2 parametrized whole-number-then-period cases using the reviewer's own exact
  counter-examples. Mutation-tested the OR/AND fix specifically: reverted to the inverted
  version, confirmed both parametrized cases fail with the exact predicted symptom, restored,
  confirmed clean (588 passed, up from 581).

  Round 4 (re-check of these two fixes only, nothing else in scope): see review.md.
