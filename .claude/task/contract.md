# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The AI-written read on a card states facts and what they mean, not the verdict. The
  card's badge already shows the verdict, and the last bullet used to repeat it. No issue; raised
  by the owner from two card screenshots (3i, ABB).

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - frontend/card_copy.py
  - tests/tooling/test_assessment_rules.py
  - tests/frontend/test_card_ui.py
  - docs/data_contract.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: the owner chose "option 1, gradual" in-thread ("1 gradual but I would like to
  the re-written examples"), saw hand-written example texts for 3i and ABB, and then said "go".
  The prompt wording is owner-signed content (section 6): the structure the owner saw is kept.
  The signed not-green sentence named "the one thing that holds the company back (for example
  falling revenue, heavy debt, or thin cash)", but falling revenue can only stop green, never
  make red (`_is_shrinking` gates green only). The owner was asked in plain words and chose "A"
  (use the corrected wording, not the signed one): red names the figure that is actually poor
  (a loss, negative free cash flow, heavy net debt, short runway, negative net cash, negative
  working capital), falling revenue is never the cause of red, yellow names the weakest figure
  or the most modest one, or says a measure could not be worked out, and never invents a
  weakness; green adds no caveat except a financial company's limit, which stays one of its
  sentences. The longer prompt adds input tokens per call, not calls. Rollout is gradual: `INPUT_HASH_VERSION`
  is NOT bumped, so a stored read is rewritten when that card's numbers change or its read was
  rejected; the deck mixes old and new styles meanwhile. Rewriting every read now costs one API
  call per card and is not done (zero-spend rule). Decided by the agent under the owner's earlier
  delegation ("act as the expert"): the guard change below, including dropping the text
  contradiction check I had first proposed, because a rejected read is called again on every
  scheduled run (cost, cap unset) and the check would also refuse a red read that calls one metric
  healthy. Not decided, the owner's if wanted: a check that ties the visible text to the verdict
  (for example banding the metrics a read cites).

changes:
  - Prompt: each sentence is one bullet; each states one fact and what it means; none states or
    restates the verdict or closes with a summary; strengths first if any; red names the actually
    poor figure, yellow the weakest or most modest, green adds no caveat; a financial company's
    limit stays one of the 2-3 sentences; a green company is never called fragile, a red one
    never healthy. The user message tells the model the verdict is for its hidden field only.
  - Tool schema: `verdict_meaning` stays required but is the model's hidden overall take.
  - Guard: `verdict_meaning_violation` keeps only the match of that hidden field against the
    verdict the rules decided. The old check that the verdict word appears in the text, and
    `VERDICT_MEANING_SYNONYMS`, are removed. No check reads the prose against the verdict.
  - Wording fixed where it was false: the regenerate-on-reject claims in `data_contract.md`,
    `generate_assessments.py` and the `INPUT_HASH_VERSION` comment (a rejected read leaves
    `ai_read` empty and is called again next run), and four comments and a test name that said
    the read ends on the verdict.
  - A test pins `INPUT_HASH_VERSION`, so a silent bump cannot regenerate every card.

done_when:
  - The prompt no longer asks to end on the verdict: `git grep -n -i -e "closing sentence" -e "End on the verdict" -e "ending on what the verdict" -- scripts docs frontend`
    prints nothing, and the prompt test checks the absence by regex.
  - `verdict_meaning_violation` accepts any text under a matching hidden classification and
    rejects a mismatch or an unknown verdict.
  - `git grep -n "VERDICT_MEANING_SYNONYMS\|VERDICT_CONTRADICTING_WORDS" -- . ':!.claude/task'`
    prints nothing.
  - Tests pin the new prompt's structure (no verdict restatement, the red and yellow cause rules,
    the financial limit inside the sentences, green-never-fragile), the hidden-field description,
    the verdict-for-hidden-field user line, and `INPUT_HASH_VERSION`.
  - `docs/data_contract.md` states the rule and the retry behaviour truthfully.
  - `pytest tests` and `python scripts/bootstrap.py --verify` pass.

known_limits:
  - Nothing reads the prose against the verdict: that a text neither states nor contradicts it
    is instructed by the prompt only. The hidden classification is the model attesting to itself.
    A check that bands the metrics a read cites would be a new mechanism (owner).
  - The prompt cannot be exercised without an API call (zero spend), so the first real outputs
    arrive in the next scheduled production run; the guards that remain catch rule breaks of the
    numeric, style and hidden-field kinds, not weak wording.
  - A read rejected by any guard leaves `ai_read` empty and is called again on every scheduled
    run, with `--max-reads` still unset. This change removes one rejection trigger (the verdict
    word missing from the text) and adds none.
  - Old reads still end on the verdict until their card's numbers change or they are rejected.
  - The red-cause list in the prompt is the same for every company type (the model only sees its
    own type's figures); making it per type would change owner-signed wording.
  - "That a measure could not be worked out" can be misapplied: a missing runway on a pre-revenue
    company means it is not spending cash, not that something is unknown, and nothing in code
    catches it. It is allowed only when nothing shown is clearly weak.
  - `supabase/migrations/010_card_assessments.sql` says reads regenerate "only when input_hash
    changes"; an applied migration, not edited.

regression_checklist:
  - Style, advice, numeric and currency guards and their tests are unchanged.
  - The frontend renders as before: `ai_read_sentences` still gives one bullet per sentence.
  - Reads already stored stay valid and render as before.
