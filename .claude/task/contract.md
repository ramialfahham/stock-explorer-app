# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #54 -- the pre-commit-hooks hooks start as `python -m pre_commit_hooks.<module>`,
  so Windows Smart App Control, which blocks pre-commit's unsigned .exe launchers, no longer
  stops a commit.

scope_paths:
  - .pre-commit-config.yaml
  - tests/tooling/test_precommit_config.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread -- override `entry` for every hook of the
  pinned `pre-commit-hooks` repo (v5.0.0) rather than turning Smart App Control off. Same code,
  same results, no new dependency.

done_when:
  - All eight `pre-commit-hooks` hooks carry `entry: python -m pre_commit_hooks.<module>`, under
    a one-line WHY comment; each module exists in v5.0.0 and has a `__main__` entry.
  - Each of the eight passes `pre-commit run --all-files` on this machine with Smart App Control
    on.
  - A test fails if a hook from that repo lacks the override.

known_limits:
  - The entries name `pre-commit-hooks`' module paths; bumping `rev` to a version that renames a
    module makes that hook fail loudly until its entry is updated.

regression_checklist:
  - Hook ids, args and excludes are unchanged.
  - The local hooks and gitleaks are untouched.
