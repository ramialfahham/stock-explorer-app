# Task contract

objective: File the owner's Gemini AI feedback (from testing two live cards, 4DMedical and
  Apple/AAPL) as a backlog doc for later discussion, per explicit owner instruction ("File these
  so we can discuss later as well"). Every checkable technical claim in the feedback was
  verified against the actual codebase first, not transcribed uncritically -- matching this
  session's established discipline. Doc-only: no verdict rule, prompt, ratio computation, or
  visualization code is changed by this task.

scope_paths:
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: everything the doc itself surfaces as an open question (which points, if
  any, are worth fixing; whether a joint liquidity evaluation should change already-shipped
  verdicts; whether sector/size threshold calibration fits the app's stated design; how narrowly
  or broadly to scope a sign-inversion guard) is explicitly the owner's call, not decided or
  actioned in this task. This task only files the verified findings and candidate directions for
  that future discussion.

done_when:
  - `docs/backlog/gemini_verdict_feedback.md` exists, following this repo's established backlog
    doc structure (Status, Summary, Context, Open questions, Candidate directions, Related).
  - Every technical claim in the Context section is verified against the actual codebase (file
    and function named, not just asserted) before being stated as true, partially true, or
    needing no verification -- not a blind transcription of the Gemini feedback.
  - No code, test, or non-doc file is touched.
  - No em dash or en dash on any added line.

impact_map:
  - Doc-only addition. No frontend, dbt, ingestion, script, or test file touched -- confirmed via
    scope_paths and the diff itself.
  - No owner-reserved decision made: the doc surfaces questions, it does not answer them.

amendments: (none)
