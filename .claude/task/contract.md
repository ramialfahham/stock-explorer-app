# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #65 (the growth research) and the owner's rule "no hallucinated reasons". The AI read
  is told the verdict color but not why the rules chose it, so it guesses reasons (3M: "mixed because
  revenue is barely growing"; the rules said debt / equity 2.68 is weak). A prompt sentence ("never
  give positive growth as the reason") patches one guess and duplicates verdict logic in prose. The
  fix: the model is given the rules' own reasons and may explain the verdict only with them.
  The verdict rules do not change: the owner chose no new growth rule after the research and an
  impact check on 1250 production cards.

scope_paths:
  - scripts/assessment_rules.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - scripts/generate_assessments.py
  - docs/data_contract.md
  - docs/context_budget.yml
  - docs/ui/discover_list.md
  - tests/frontend/test_card_copy.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat: yes, tell the AI the real reasons; no new growth
  rule (B). The prompt wording below is owner-signed content (section 6): it takes effect on the
  owner's "go". No verdict band, threshold or color changes; no seed, frontend, export or dbt change.
  `docs/data_contract.md` budget 67000 to 68100 for the new paragraphs (reason in the MR).

changes:
  - One evaluation: each `_verdict_*` function keeps its exact rules but returns the bands it used
    (per metric: core or supporting, good/ok/weak/not judged, a note when a sign-inversion guard or
    the current-ratio relief applied), the revenue-shrinking flag, the metrics that made it red, and
    the ones that held it back from green. `compute_verdict` returns that evaluation's verdict, so the
    reasons and the color cannot drift apart. Existing verdict tests stay unchanged and green.
  - The user message gains, under the numbers: "Why lines (how the rules reached the verdict; explain
    only with these; never state the verdict itself):", one line per judged metric (label as in the
    numbers list, band word, note), "Rev growth YoY (quarter): falling" only when it is, and one
    closing line: "Held back from the top by: ...", "Placed at the bottom because of: ..." or, for a
    green card, that nothing held it back. No thresholds are shown. (Header and growth line differ
    from the wording first shown to the owner; the owner is asked to acknowledge at commit.)
  - Prompt: the bullet "Falling revenue counts against a company here ... blaming the verdict on it is
    not." becomes "The Why lines under the numbers say how the rules reached the verdict. Explain what
    is strong or weak only with those lines, and give no other reason for the verdict. Falling revenue
    can stop a company being called healthy but never makes it red. Rising revenue does not make a
    company healthy, and is never a reason to buy." The other bullets are unchanged.
  - `INPUT_HASH_VERSION` 5a.5 to 5a.6 (a merge before the Oct 15 06:00 UTC run lets one run cover both).
    The hash also covers the reasons (each judged metric's band and note, whether revenue is falling)
    and the operating-margin basis, so a read regenerates when a reason changes without a color change.
    The dead `_verdict_*` wrappers and `_VERDICT_FN` are removed; comments name `_evaluate_*`. A
    missing runway now reads "no cash burn is shown" (not "is not burning cash"); the green closing line
    says "no falling revenue is shown". Comment and doc pointers in three extra files were repointed.
  - Tests: the reasons are consistent with the color (red names only weak core metrics, yellow names what
    held it back, green names nothing) on the 73 golden-mart rows and synthetic grids for every type; the Why block for the live 3M, 4DMedical and AAPL numbers; growth listed only
    when shrinking; guard notes; the pins on the old growth sentences replaced. Docs paragraph; handover.

done_when:
  - The old growth sentence ("never give it as the reason") is gone from scripts, tests and docs; every verdict test
    that passed before passes unchanged; the Why block for 3M names debt / equity as weak and nothing
    about growth; `pytest tests -q` and `python scripts/bootstrap.py --verify` pass.
  - No band, threshold, seed, frontend, export, dbt or migration change.

known_limits:
  - The model can still phrase a claim around a figure that the marker list does not know; the reasons
    shrink the room for invention but do not remove it. The rejection rate is counted after the run.
  - The reasons name bands, not thresholds; the card's own gloss and the Limit lines carry meaning.
  - A metric with no value can still be named ("not judged", or weak because equity is zero or
    negative) though the numbers list does not show it; "weak" for a guard is a caution, not a
    verdict on the cause; the card face keeps its own net-cash line (#66).
  - #65 stays open for any later growth rule; sector medians in the read remain a follow-up (#66).

regression_checklist:
  - Verdict colors for every existing test row unchanged; advice, style, figure and verdict-meaning
    guards unchanged; the other prompt rules unchanged.
