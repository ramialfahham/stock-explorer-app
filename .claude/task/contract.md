# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Bug reported by the owner on live cards (AAPL, 3M, 4DMedical): the AI read invents
  purposes ("to fund growth"), ends with a verdict sentence the prompt already bars, says "one third"
  for figures, and writes "A$" with no amount. Causes: the prompt gives the model hand-written
  glosses and never the catalogue's text; it says "don't recite every number back"; nothing requires
  a figure in a sentence or limits its length; and a stored read regenerates only when `input_hash`
  changes (2026-10-11 log: `read carried for us_sp500/AAPL (unchanged)`).

standards: The owner's writing standards (`football-data-pipeline/docs/working_agreement.md` section
  9): ISO 24495-1 plain language; ISO/IEC 11179-4 (a definition says what the thing is, no rationale);
  ASD-STE100 (one word per meaning, one topic per sentence, active voice, 25 words in a description). Applied:
  the model gets only definition-style catalogue text (`gloss`, `applicability`), never
  `interpretation`; the prompt follows the STE rules; code checks sentence length.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - docs/data_contract.md
  - docs/context_budget.yml
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat: the AI feature stays; figures in digits; one-time
  regeneration by bumping `INPUT_HASH_VERSION`; deterministic rejection, NO retry, no extra API call;
  the catalogue is the only source of meaning; the three standards apply; the prompt wording below
  (approved as shown, "go ahead"); answer A: the facts block differs from the card face in one
  place (below) and a follow-up fixes the card; growth keeps its direction cue (restored). `docs/data_contract.md` budget 65500 to 67000 for
  the new paragraph (reason in the MR). No seed, frontend, export or dbt change.

changes:
  - Facts block: per metric `- {label}: {value}`, `  Meaning: {gloss + direction cue}`, `  Limit:
    {applicability}`, from `frontend/metrics.json` (kept equal to the seed by the existing lock).
    `read_metric_meaning` mirrors `frontend/card_copy.py` `metric_gloss`, pinned equal by a test,
    except: a negative debt ratio with non-positive EBITDA is not called net cash. `gloss` leaves
    `READ_METRIC_BRIEF`.
  - Prompt, replacing "Interpret, don't list...": (1) "Write short sentences. Each sentence has one
    topic, is in the active voice, and has at most 25 words. Each sentence states one of the numbers
    below in digits, exactly as it appears (for example 24.0%), and says what it means in plain
    words, using the wording of that number's Meaning line. Use one word for one thing: call a number
    by the name it has in the list, every time. Pick the 2 or 3 numbers that most shape the picture."
    (2) "Explain a number with the Meaning and Limit lines given for it under the numbers list, and
    say any finance term in plain words. Use a Limit line only when it applies to this company. Never
    say why the company has a number, how it got there, what it plans, or what the company can or
    cannot do. Write in words, never the symbols ≈, → or ÷." (3) "Write every number in digits, never as
    a fraction or a phrase in words ("one third", "a quarter of", "a fifth", "half", "one in five").
    A time period such as "the latest quarter" is not a number. Never write a currency symbol or code
    without an amount next to it." The "may be empty" sentence is removed; the financial lens ends
    "Its revenue is net interest plus fees, never sales, even where a Meaning line says sales."
  - `INPUT_HASH_VERSION` "5a.4" to "5a.5": the next run regenerates all 1241 reads (about $5, about
    95 minutes; no `--max-reads` cap, which would clear stored reads).
  - `find_read_figure_violations(row, read)` in `_generate_read` after the style check, rejecting
    like every other check: (1) a sentence with none of the card's figures (digit boundaries, leading
    minus ignored), unless it contains "balance-sheet", "capital strength" or "could not be worked
    out"; (2) a sentence over 25 words; (3) a fraction in words: thirds, fifths, tenths, halves,
    a/one third|fifth|tenth|half (space or hyphen), "half of", "half the", a/one quarter of, three
    quarters, "one in five" forms (time references pass); (4) "to fund", "to finance", "in order to",
    "because", "thanks to", "driven by", "ability to", "so it can", "allowing it"; (5) a currency
    symbol or code without a digit next to it (one space allowed before, spaces after).
  - Tests for each rule (violating and compliant), the three live reads as violating cases, the
    prompt and catalogue pins, figure-stating fake reads; docs paragraph; handover.

done_when:
  - `git grep -n "recite every number" -- scripts docs tests` finds only the test asserting it is
    absent; `git grep -nE "5a\.4" -- scripts tests docs` finds nothing; `git grep -n '"gloss"' --
    scripts/assessment_rules.py` finds only the catalogue read in `read_metric_meaning`.
  - A test fails if the facts block differs from the catalogue text, or if any `gloss` or
    `applicability` a read uses trips the advice or style guards.
  - The check rejects the three live reads and accepts compliant reads; `pytest tests -q` and
    `python scripts/bootstrap.py --verify` pass.
  - No seed, frontend, export, dbt or migration change; advice, style and verdict-meaning guards
    unchanged.
  - After the owner triggers a production run (not part of the merge): count `read REJECTED` lines,
    check the live AAPL, 3M and 4DMedical cards and a sample, report the rate.

known_limits:
  - No check can guarantee free prose never invents a claim; a clause attached to a figure can carry
    one the marker list does not know. The plain-word explanation of a finance term (EBITDA) is the
    model's own and unchecked. The symbols ban and active voice are prompt-only.
  - The rejection rate is unknown until the run; a rejected card shows the plain fallback line.
  - Word lists are partial: bare "half" ("nearly half") and "a quarter" without "of" pass.
  - Sector medians in the read are left out (not covered by `validate_read_metrics`). Follow-ups:
    that, a catalogue audit against ISO/IEC 11179-4, and the card face's net-cash line.
  - The first run needs about 95 of the job's 120 minutes; a merge before the Oct 15 06:00 UTC
    schedule makes that run regenerate every read unattended.

regression_checklist:
  - Advice, style and verdict-meaning guards and their tests unchanged.
  - Every `_generate_read` test passes with a figure-stating read; other prompt rules unchanged.
  - The card face and frontend untouched.
