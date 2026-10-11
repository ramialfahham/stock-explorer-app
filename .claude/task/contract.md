# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #48 (milestone "3 · Professional baseline", guardrails). Every guard that is
  wired in has a test that fails when it stops working, every reviewer definition loads, and
  every routing pattern matches a file. Four rules, each enforced by a test.

scope_paths:
  - tests/tooling/claude_hooks/test_agent_definitions.py
  - tests/tooling/claude_hooks/test_pre_push_gate.py
  - tests/tooling/claude_hooks/test_review_routing_patterns.py
  - tests/tooling/test_every_guard_has_a_test.py
  - tests/tooling/test_check_layer_contract.py
  - tests/tooling/test_check_dbt_sql_structure.py
  - tests/tooling/test_check_registry_var_sync.py
  - tests/ingestion/test_rate_limit.py
  - .claude/agents/equity-analyst-reviewer.md
  - .claude/review_routing.json
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Both answered by the owner in chat. (1) The dead pattern
  `.github/workflows/*` is removed, with its mention in the routing comment (answer A). (2) The
  registry-sync script gets its own test and the existing onboarding test stays (answer A). No
  guard script is changed.

rules:
  R1: every file in `.claude/agents/` has frontmatter that `yaml.safe_load` parses, with `name`,
    `description`, `tools`, `model`, and `name` equals the file stem.
  R2: every script wired in `.claude/settings.json` hooks or in a local hook of
    `.pre-commit-config.yaml` (entry `python <path>.py`) has a test file, other than
    `test_hooks_import.py` and the meta-test itself, that names its module. One behaviour test
    per script, each with a violating and a compliant case.
  R3: every pattern in `review_routing.json` (`paths`, `artifact_only`, `artifact_only_never`)
    matches at least one file from `git ls-files`.
  R4: `call_with_retry` raises a non-rate-limit error after one call, retries a rate-limit
    error (`429`, `Too Many Requests`, `YFRateLimitError`) and raises it after `max_attempts`,
    and returns the value after one 429. `time.sleep` is patched.

changes:
  - `equity-analyst-reviewer.md`: the `description` value is quoted; the em-dash on that line
    becomes `--` (project rule for any edited line).
  - `review_routing.json`: the `.github/workflows/*` pattern and its mention in
    `_comment_guard_paths` are removed.
  - The tests above. Fixture SQL is built in `tmp_path`; no tracked fixture files.
  - Handover: #48 collapsed to one line; the unloadable-reviewer note removed.

done_when:
  - The tests above pass, including the R1 test on `equity-analyst-reviewer.md` and the R3 test
    on every routing pattern.
  - `git grep -nF ".github/workflows"` outside the keep list finds nothing.
    Keep list: `.gitlab-ci.yml:1` (a header note that CI was ported from GitHub; not a routing
    claim) and this contract.
  - `pytest tests -q` and `python scripts/bootstrap.py --verify` pass.
  - No guard script (`scripts/check_*.py`, `.claude/hooks/*.py`, `ingestion/`) is modified.

known_limits:
  - R2 proves a test names the script, not that the test is good; the behaviour tests carry
    that. The meta-test finds wired scripts from `settings.json` and the `entry:` lines of
    local pre-commit hooks; a guard wired some other way is not seen.
  - The routing test is stricter than criterion GRD-3 in `docs/quality_criteria.json`: it has no exemption for a pattern documented as
    dormant. No pattern is dormant today.
  - R1 checks that the frontmatter parses and has the four keys, not that the harness accepts
    every value.
  - `check_dbt_sql_structure.py`: its scalar-subquery regex is anchored at the start of the file
    (`^\s*select`), but every compliant model starts with WITH, so the rule can only fire on a
    file that already fails the WITH rule. The test pins the case that fires; fixing the regex
    changes a gate and is a separate issue.
  - The registry-sync duplicate: `test_dbt_active_markets_match_the_registry` stays as a second copy of the
    invariant.

regression_checklist:
  - Existing hook and tooling tests unchanged and passing.
  - Every reviewer named in `review_routing.json` still has a role file
    (`test_every_routed_reviewer_has_a_role_file`).
  - The remaining routing patterns are unchanged.
