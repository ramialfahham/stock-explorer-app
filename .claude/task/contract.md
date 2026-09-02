# Task contract

objective: Structured AI-read output + hallucination guard (Gemini feedback points 3/4,
  `docs/backlog/gemini_verdict_feedback.md`), plus a frontend fallback for the card state this
  guard makes more common. `scripts/generate_assessments.py`'s Claude Haiku call currently
  returns free text with no structured output and no post-generation check against the card's
  real numbers -- the model could state a number that doesn't match the data, and nothing
  catches it before it's stored and shown to a beginner as fact.

  Confirmed design, worked out with the owner across this session's conversation, not invented
  unilaterally:
  1. **Structured output.** Switch the call to forced tool-use: the model returns
     `{"read": "...", "referenced_metrics": [{"label": "...", "value_as_shown": "..."}]}`
     instead of free text. `referenced_metrics` lists, verbatim, every metric from the facts
     block the read explicitly cites -- the label and rendered value copied EXACTLY as shown,
     not reformatted or recomputed.
  2. **Numeric cross-check, not an LLM judge.** Each `{label, value_as_shown}` pair is checked
     against the SAME rendering `build_read_messages` already showed the model for that label
     (reusing `_format_metric_value`, no new formatting logic, no tolerance/rounding heuristics
     needed since both sides use the identical renderer). This catches the concrete, provable
     failure mode (the model stating a number that doesn't match the data) at the cost of one
     API call per read, same as today. It does NOT catch an unsupported qualitative claim that
     cites no wrong number -- that would need a second LLM-judge call, roughly doubling cost;
     owner explicitly chose the cheaper, narrower guard over that.
  3. **Fail-closed, no retry.** Any mismatch, unknown label, or malformed tool response is
     treated exactly like an API exception already is: `_generate_read` returns `(None, None)`,
     the record's `ai_read`/`read_model` stay absent, and the existing regenerate-on-input-hash-
     change self-healing picks it up next run. No new state, no retry loop, no added cost on the
     unhappy path beyond what already exists.
  4. **Frontend fallback for the resulting "verdict but no read" state.** This state already
     existed before this task (a brand-new card, or any API failure) and today renders as the
     badge with NOTHING else -- which the owner flagged as reading like a bug, not a deliberate
     "not yet written" state, once this guard makes the state more frequent. Fix: when `ai_read`
     is absent, show a deterministic, non-AI one-liner under its OWN honest heading, "What the
     verdict means" (never "AI-written", which would misattribute it). The body text explains
     what actually drove the verdict color (a plain description of the real rule, e.g. "Every
     core financial-health metric on this card came in strong, and nothing else raised a
     concern." for green), not a restatement of the badge's own label -- an earlier draft that
     just reused `VERDICT_MEANING`'s fragment verbatim was rejected for being a restatement, not
     an explanation, exactly what the new heading promises.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/styles.py
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_card_copy.py
  - docs/data_contract.md
  - docs/north_star.md
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none remaining for the mechanism -- structured output, numeric-only
  cross-check (not an LLM judge), fail-closed with no retry, and the frontend fallback's exact
  heading ("What the verdict means") and body wording per verdict were all explicitly confirmed
  by the owner this session, after the owner twice rejected a first-pass answer as the easier
  option rather than the correct one (once for the debt_to_equity guard's severity in an earlier
  task, again here for the fallback wording) -- both corrected before proceeding. This DOES
  change what beginners see on cards whose read was ever unverifiable: they now see a real,
  though generic, explanation instead of a bare badge.

done_when:
  - `scripts/assessment_rules.py`: a `_present_metric_renderings(row, ctype, currency) ->
    dict[label, rendered]` helper extracted from `build_read_messages` (behavior-preserving --
    the facts block and user message must render identically to before). A `READ_TOOL_NAME` /
    `READ_TOOL_SCHEMA` pair (pure data, no I/O) describing the `write_card_read` tool. A
    `validate_read_metrics(row, referenced_metrics) -> bool` using the same helper: True when
    every `{label, value_as_shown}` pair matches this row's own rendering for that label exactly;
    False on any unknown label or mismatched value; True (vacuously) for an empty list, since a
    read may legitimately discuss the verdict without citing a specific number. A missing row
    denominator/value is not a special case here -- the label simply would not have been in the
    facts block, so any reference to it is already an unknown-label failure.
  - `READ_SYSTEM_PROMPT` or the user message gets the minimum addition needed to tell the model
    about the tool-call format and the "copy the label and value exactly as shown, do not
    reformat or recompute" rule.
  - `scripts/generate_assessments.py`: `_generate_read` calls `client.messages.create(...,
    tools=[READ_TOOL_SCHEMA], tool_choice={"type": "tool", "name": READ_TOOL_NAME})`, extracts
    the `tool_use` block's `.input`, and returns `(None, None)` when the block is missing, `read`
    is blank, or `validate_read_metrics` rejects it -- same return-shape contract as today, so
    `attach_reads` needs no changes. `READ_MAX_TOKENS` bumped enough to fit the JSON structure
    (a few referenced-metric entries plus the prose) without truncating the read itself.
    `INPUT_HASH_VERSION` NOT bumped -- this is a generation-mechanism change, not an input change;
    already-stored reads stay valid and are not force-regenerated (a full-universe regenerate is
    a real cost decision, not implied by this fix).
  - `frontend/card_copy.py`: `VERDICT_FALLBACK_READ` (green/yellow/red -> the confirmed body
    text), structurally complete against `VERDICT_BADGE_LABEL`'s three keys.
  - `frontend/card_ui.py`: `BLOCK_LABEL_VERDICT_MEANING = "What the verdict means"`.
    `_health_block_html` restructured so a present `ai_read` renders exactly as before (no
    behavior change to that branch), and an absent one now renders the badge plus the fallback
    heading and body (new `ss-verdict-fallback` class, not `ss-ai-read`, so a test or a future
    reader can tell AI-written prose apart from the deterministic fallback from the class name
    alone) instead of the badge alone -- unless the verdict token itself is unrecognized, which
    still renders nothing at all (unchanged).
  - `frontend/styles.py`: `.ss-health-block .ss-verdict-fallback` styled identically to
    `.ss-health-block .ss-ai-read` (the fallback should look like a natural, equally-weighted
    piece of card content, not visually flagged as lesser) -- same selector group or a duplicated
    rule, implementer's choice.
  - Tests: `validate_read_metrics` covered directly (matching pair, mismatched value, unknown
    label, empty list, a currency-formatted value). `_generate_read`/`attach_reads` covered with
    a faked tool-use response (the existing `_FakeBlock`/`_FakeMessage` fakes in
    `test_generate_assessments.py` restructured to produce a `tool_use` block with an `.input`
    dict) for both a valid read and a rejected one (mismatched `value_as_shown`), the latter
    landing in `attach_reads`' existing `failed` count, not a new counter. Frontend:
    `test_health_block_shows_badge_without_ai_read_when_null` and
    `test_ai_label_never_appears_without_ai_text` REWRITTEN (their core assertion -- "nothing
    else renders" -- is no longer true by design) to assert the fallback heading and body render
    instead, while still asserting `BLOCK_LABEL_ASSESSMENT` never appears over non-AI text (that
    part of the claim is unchanged). `test_health_block_ignores_unrecognized_verdict_token`
    verified still passes unmodified (an unrecognized token means no verdict at all, so no
    fallback either -- unaffected by this change). New: `VERDICT_FALLBACK_READ`'s key set
    verified against `VERDICT_BADGE_LABEL`'s.
  - `docs/data_contract.md`'s Slice 5b description updated: structured tool-use output, the
    numeric cross-check, and fail-closed-no-retry on a mismatch.
  - `docs/north_star.md`'s Scan/Gloss/Deep tier table updated: "AI read (always visible)" no
    longer fully accurate on its own -- note the fallback state.
  - `docs/backlog/gemini_verdict_feedback.md` updated: points 3/4 marked acted on, with a pointer
    to this branch.
  - `pytest` green. No dbt or Supabase migration changes -- `card_assessments` schema is
    untouched, structured output is validated at generation time and never persisted as its own
    column, only the final approved prose (or nothing) reaches `ai_read`.
  - No em dash or en dash on any added line.

impact_map:
  - Changes what beginners see on any card whose AI-read generation is ever unverifiable or
    still pending: badge + a real, honest (if generic) explanation, instead of badge alone.
    Existing valid, already-stored reads are completely unaffected -- this only changes the
    FALLBACK path and future generations' validation, never retroactively touches stored prose.
  - A previously-passing generation could now fail validation and regenerate as unread on the
    NEXT run instead of showing prose this run, if the model's structured output doesn't match
    -- expected to be rare (the model is given the exact numbers to copy), not measured here;
    worth watching after the next real pipeline run.
  - This touches Streamlit rendering (`frontend/card_ui.py`, `frontend/card_copy.py`,
    `frontend/styles.py`), so `docs/working_agreement.md`'s UX PR gate applies: north-star check
    (this task updates `north_star.md` itself, since it's the current source of truth for this
    element), one primary job + mobile wireframe in the MR body, 480px smoke test before commit.
  - Known, explicitly out of scope: no dedicated `docs/ui/*.md` component-spec file exists for
    the health block today (unlike Discover header/list, which each have one) -- `north_star.md`
    is the only current spec for this element, brief as it is. Creating a full dedicated
    component doc is a separate, worthwhile follow-up, not required to properly document this
    specific change, and not built here to avoid further scope growth on an already-large task.
  - Known, explicitly out of scope: an LLM-judge second pass that could catch unsupported
    qualitative claims (not just wrong numbers) -- owner explicitly chose the cheaper, narrower
    numeric guard over this; revisit only if the numeric guard proves insufficient in practice.

amendments:
  - The frontend fallback body text (point 4, `VERDICT_FALLBACK_READ`) shipped as an
    owner-authored general one-line business-language summary per verdict color, not a
    description of the verdict engine's internal rule mechanics as point 4's original example
    sketched. Surfaced mid-task: the engine's decisive-vs-supporting metric split, and its
    per-metric thresholds, have zero representation anywhere in the UI (`metrics_for_card()`
    renders every metric flatly for a card's company type; the catalogue's `importance_tier` /
    `VISIBLE_METRICS` / `DEEP_DIVE_METRICS` split is defined but unused anywhere else in
    `frontend/`), so prose describing "the real rule" in those terms would assert something no
    reader can check. Final wording is the owner's own (§6), confirmed after several drafts.
  - `scripts/assessment_rules.py`: also trimmed one pre-existing comment (current-ratio
    FCF-coverage relief, commit `535930170`) that embedded one company's real figures and a
    version-history narrative -- owner instruction, triggered by this task's own fallback-wording
    discussion surfacing it as confusing (it read, on first mention, as a hardcoded special case).
    Unrelated to this task's mechanism change, but the file was already in `scope_paths`; trimmed
    to the current rule and its rationale only, no named example.
