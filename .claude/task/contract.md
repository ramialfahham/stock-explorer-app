# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The on-demand production run of 2026-10-11 (pipeline 2936387293, cancelled by the owner at
  353 reads, nothing stored) accepted 0 of 353 reads: 307 had a sentence over 25 words (251 for that
  alone), 46 a fraction in words, 18 a sentence with no figure, 17 a lone currency symbol, 14 advice
  words, 12 a cause word. The model does not keep to the 25-word rule; the scheduled Oct 15 06:00 UTC run
  would repeat this and replace nearly every stored read with the plain fallback line. A read-only test
  on 60 real cards (100 real calls, about $0.40, nothing written) measured: revised prompt wording
  accepts 73% at a 25-word limit and 83% at 30, against 35% and 60% for the current wording.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - README.md
  - docs/data_contract.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat: a test with real calls (A, key in `.env`); ship the
  revised wording shown in chat; the check's length limit 25 to 30 words; ONE retry for a rejected read
  (B, after seeing the cost: about +$0.80 per full refresh, and the failed cards are retried at the next
  scheduled run anyway). The retry reverses the earlier "no retry" rule: that is recorded here. One more
  validation of about 45 real calls (about $0.20, nothing written) is part of the work. The run cap
  (30% of reads + 20) was chosen by the owner (A), and retries count inside `--max-reads` (A). The worked
  example in the prompt stays as shipped: a reworded example (two short sentences, the list name, no
  "per 100") was tested on the same 44 real cards and accepted 39 (88%) with 14 retries against 44
  (100%) with 5, so the owner's rule (back to A when acceptance falls) applied; the wording items are
  issue #67. No verdict, seed, frontend, export or dbt change.

changes:
  - Prompt: the bullet "Write short sentences..." becomes "Write 2 or 3 sentences, each under 20 words.
    Each sentence has one number in digits, exactly as it appears in the list (for example 24.0%), then
    what it means in plain words, using that number's Meaning line. Example: "Operating margin is 20.4%,
    so 20.4 of every 100 of sales is left as operating profit." Never join two ideas in one sentence with
    "but", "which", "and" or a comma: start a new sentence. Call a number by the name it has in the list,
    every time. Pick the 2 or 3 numbers that most shape the picture."
    The currency sentence is unchanged (the prompt names no currency; an existing test requires it).
    The check allows 30 words (`READ_MAX_WORDS`), so the prompt asks for less than it refuses.
  - One retry: when the model answered and a check refused the read (figures, style, cited-metric or
    verdict-meaning guard), `_generate_read` asks once more and uses the second answer if it passes. No
    retry after an API error or a malformed answer. A per-run budget of 30% of the reads attempted plus
    20 retries stops a run from doubling its calls; a retry counts against `--max-reads`; the log
    prints the retries used. `docs/context_budget.yml`: data_contract.md 68100 to 68400 (reason in the MR).
    The prompt no longer states "active voice" or "one topic per sentence"; it states a length
    and "never join two ideas" instead.
  - `INPUT_HASH_VERSION` stays 5a.6: no read was stored under it (the run stored nothing).
  - Tests: the retry (accepted second time, refused twice, API error not retried, budget exhausted, budget
    formula), the 30-word boundary, the prompt pins; docs and handover say "one retry".

done_when:
  - `git grep -nE "no retry|No retry" -- scripts tests docs` finds only text that says the opposite or the
    API-error case; `git grep -n "at most 25 words" -- scripts tests docs` finds nothing.
  - A real-call check of about 45 cards through the real `_generate_read` with the retry accepts at
    least 88% (my estimate for the revised wording, 30 words and one retry is about 93%); the result and
    the rejection reasons are written into `review.md`. If it is below 80%, stop and ask the owner.
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` pass; no verdict, seed, frontend, export
    or dbt change.
  - After the merge: the owner triggers one full run; the first 100 reads are watched and the run is
    stopped by the owner if fewer than 60 of them are accepted. Then the usual check of the live cards.

known_limits:
  - The retry cannot fix a model that keeps breaking a rule; a card whose two answers are both refused shows
    the plain fallback line until the next scheduled run, which tries it again.
  - The accepted texts can still hold claims the data does not support and no check catches: a
    prediction or capability about the company ("may struggle to pay what it owes soon" for a current
    ratio of 0.40, "cash it can spend freely"), loose strength words ("converts most sales into cash"
    for 9.7%, "obligations are pressing"), and "sales" on a financial company. The rate is sampled
    after the run; a word guard for these is a follow-up (#66).
  - Figures for a full run of about 1240 reads (an estimate from the model's list price and the token
    size of a read, not from the bill): about $4.85 without retries; the retry doubles the calls for
    about 17% of reads (about 211 retries), +$0.80 and +11 minutes, so about $5.65, rounded to $5.70;
    the cap is 30% of reads + 20 = 392 retries. Minutes: about 96 without retries, about 106 with the
    expected ones, about 116 at the cap; the job limit is 120. A binding `--max-reads` leaves no room for retries (production
    sets none). The real-call validation sample was 31 operating, 11 financial and 2 pre-revenue cards,
    25 of them non-USD.

regression_checklist:
  - The advice, style, cited-metric and verdict-meaning guards and the verdict rules are unchanged.
  - Every existing test passes except the ones that pin the old limit or "no retry", which change here.
