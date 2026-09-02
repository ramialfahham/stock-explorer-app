# Review

diff_sha256: cd750c1f6f1c4a0b93776bcfc74eabb6cca0662f2a38906cdc993726e74e3f35

Three reviewers required per `.claude/review_routing.json` for the staged files: `scope-auditor`
(always), `cto-reviewer` (`scripts/*`, `tests/*`, `frontend/*`), `equity-analyst-reviewer`
(`docs/data_contract.md`). All dispatched as cold, blinded `general-purpose` subagents reading
their role file verbatim, against the staged diff only.

## scope-auditor
VERDICT: PASS
risks_checked:
- All 13 staged files match `scope_paths` exactly; nothing touched outside it.
  `tests/frontend/test_card_copy.py` is listed in `scope_paths` but untouched -- permitted (scope
  is a ceiling, not a mandate) and not required by `done_when` (the `VERDICT_FALLBACK_READ`
  key-parity test landed in `test_card_ui.py` instead).
- `build_read_messages` refactor is behavior-preserving: full pytest suite green, including the
  unmodified pre-existing `test_build_read_messages_omits_missing_metrics`.
- `INPUT_HASH_VERSION` left unbumped (`"5a.4"`), per `done_when`'s explicit cost guard.
- No em/en-dash on any added line (scanned every `+` line in the staged diff).
- `attach_reads` needed no changes, confirmed only `_generate_read` touched; the new reject-path
  test lands in the existing `failed` counter, not a new one.
- `ss-verdict-badge` / `ss-verdict-fallback` ordering assertion checked against the real render
  path, not an aspirational string.
- Fallback wording is not a restatement of `VERDICT_MEANING`'s fragments -- compared directly.
- The amendment's cited commit (`535930170`) verified to exist via `git log`.
- No `decisions_reserved` item silently decided; the diff's implementation matches each
  owner-confirmed decision recorded in the contract.

## cto-reviewer
Two rounds. Round 1 (diff hash `88ced2edc0ea787f498580e708a489acc36684412b8021ecef559fc8dc5ccfb9`):
**FAIL** -- two findings:
1. `scripts/generate_assessments.py`'s `_generate_read`: the "no tool_use block" and "malformed
   tool payload" branches returned `(None, None)` with no stderr log, unlike the other two
   failure branches (API exception, `validate_read_metrics` reject), and had zero test coverage.
2. `scripts/assessment_rules.py`'s `_present_metric_renderings` keys its dict by metric LABEL
   text, not internal field name; label uniqueness per `company_type` was an unenforced,
   untested, load-bearing invariant -- a future label collision would silently corrupt both the
   facts block and the hallucination-guard validation.

Both fixed: stderr logging added to both branches (mirroring the existing two), three new tests
(`test_attach_reads_rejects_a_response_with_no_tool_use_block`,
`test_attach_reads_rejects_a_blank_read`, `test_attach_reads_rejects_non_list_referenced_metrics`,
each asserting on `capsys.readouterr().err`); a label-uniqueness assertion added to
`test_read_brief_covers_every_input_field`, checked per `company_type` against
`INPUT_FIELDS_BY_TYPE`.

Round 2 (diff hash `cd750c1f6f1c4a0b93776bcfc74eabb6cca0662f2a38906cdc993726e74e3f35`):
VERDICT: PASS
risks_checked:
- Both round-1 findings confirmed fixed by inspection of the fix and its test coverage.
- Fail-closed guard integrity: traced every rejection path in `_generate_read` (no tool_use
  block, blank read, non-list `referenced_metrics`, `validate_read_metrics` failure) and
  confirmed each leaves `ai_read`/`read_model` absent from the record, never a partial write.
- Re-run/self-healing safety: `INPUT_HASH_VERSION` untouched, so no forced mass regeneration;
  a rejected read still self-heals via the existing regenerate-on-hash-or-null-read path.
- Behavior-preservation of the extracted renderer: `build_read_messages` and
  `validate_read_metrics` share one renderer (`_present_metric_renderings`), so the guard cannot
  silently drift from what the model was shown.
- Every `done_when`-named test present; full suite green (473 passed).
- No em/en-dash on any added line; no new dependency, no CI/hook/config change, no secret.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Mechanism precision: the new `docs/data_contract.md` paragraph's description of forced
  tool-use (`tool_choice`, `write_card_read`) verified against
  `scripts/generate_assessments.py:180-212` and `scripts/assessment_rules.py:707-729` line by
  line -- matches exactly.
- "Numeric cross-check, not an LLM judge" confirmed accurate: both `build_read_messages` and
  `validate_read_metrics` call the identical `_present_metric_renderings` helper; no second LLM
  call anywhere in the diff, no tolerance/rounding logic, exact string equality only.
- Fail-closed, no retry: traced all failure branches in `_generate_read`, all converge on
  `(None, None)`; confirmed the doc's word "absent" (not "null") is the precise description,
  since the upsert distinguishes an omitted column from an explicit null.
- Frontend fallback linkage and non-attribution: `BLOCK_LABEL_VERDICT_MEANING` matches the doc's
  quoted heading exactly; the fallback path never uses `BLOCK_LABEL_ASSESSMENT` ("AI-written").
- No em/en-dash in the new paragraph; no buy/sell/hold language, no invented thresholds, no claim
  beyond what the code implements, consistent with the educational/non-advice framing.
