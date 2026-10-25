# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The commit-time secret scan cannot run on the owner's machine. The `gitleaks` hook is built by
  `pre-commit` from source (Go) into an unsigned `gitleaks.exe`, and Windows Smart App Control (enforce mode) refuses
  a program it has no reputation for (`WinError 4551`). It passed only by chance, and every commit now fails. The
  official release `v8.30.1` of the same tool runs under Smart App Control (checked: it starts, its SHA-256 matches
  the published checksum, and it found no leaks in a staged change). One rule: the scan runs the official pinned
  release, verified against pinned hashes, through a Python launcher, the way every other hook here already runs
  (`python -m`, because Smart App Control blocks unsigned launchers).

scope_paths:
  - scripts/run_gitleaks.py
  - tests/tooling/test_run_gitleaks.py
  - tests/tooling/test_precommit_config.py
  - .pre-commit-config.yaml
  - .gitignore
  - .gitlab-ci.yml
  - docs/development_workflow.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat. The design (A): `scripts/run_gitleaks.py` downloads the official
  release for the platform once into a gitignored folder inside the project (`.cache/gitleaks/<version>/`), checks
  it against SHA-256 hashes pinned in the script, and runs it on the staged change with the repo's
  `.gitleaks.toml`; the compiled hook is replaced by a local hook that calls the launcher; a test keeps the
  launcher's version equal to the CI scan image. The owner approved the one-time download of the release zip and its
  checksum file for the test (scratch folder only). Nothing is installed outside the project folder. No skipped
  hook: the new hook replaces the blocked one in the staged config, so this commit passes the scan itself.

changes:
  - `scripts/run_gitleaks.py`: `VERSION = "8.30.1"`; `ASSETS` maps (system, machine) to the release file name and
    its SHA-256 (windows x64/arm64, linux x64/arm64, darwin x64/arm64, copied from the release's checksum file);
    `ensure_binary()` returns the cached binary or downloads the asset, refuses a hash mismatch, extracts only the
    one binary member, writes through a temp name and `os.replace`; `main()` runs
    `gitleaks git --pre-commit --redact --staged --verbose --config .gitleaks.toml` from the repo root and returns its
    exit code; any error exits non-zero with a message (the scan fails closed).
  - `.pre-commit-config.yaml`: the `https://github.com/gitleaks/gitleaks` repo block becomes a `repo: local` hook with
    id `gitleaks`, the same display name, `entry: python scripts/run_gitleaks.py`, `language: python`,
    `pass_filenames: false`, `always_run: true`; the header comment names the launcher. CI's
    `validate:pre-commit` still skips the id `gitleaks` (the full-history scan runs in `validate:secret-scan`).
  - `.gitignore`: `.cache/`. `.gitlab-ci.yml`: only the comment above the scan image names `VERSION` in the launcher.
  - Tests: version equals the CI image tag; hash mismatch refused and nothing left behind; the cached binary is
    reused without a download; only the binary member is extracted from a zip and a tar.gz; an unsupported platform
    exits non-zero; `main()` passes the expected arguments and returns the scan's exit code; the pre-commit config has
    the local hook and no remote gitleaks repo.
  - `docs/development_workflow.md`: the sentence about the staged gitleaks scan names the launcher and why.

done_when:
  - `git commit` of this branch passes every hook including the new `gitleaks` hook (no skipped hook).
  - `python scripts/run_gitleaks.py` on the staged change exits 0 on this machine, and exits non-zero on a staged
    file holding a test secret (checked once by hand and pinned by the argument test).
  - `git grep -n "github.com/gitleaks/gitleaks" -- .pre-commit-config.yaml` finds nothing; the version string appears
    in the launcher and `.gitlab-ci.yml` only (`git grep -n "8.30.1" -- scripts tests/tooling docs .pre-commit-config.yaml .gitlab-ci.yml`).
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` and the em-dash and narrative-date checks pass.

known_limits:
  - A binary already present in `.cache/gitleaks/<version>/` is run without a second hash check; the cache is inside the
    project folder, where the hook itself could equally be edited.
  - The Linux and macOS archive layout (the binary at the archive root) is assumed from the Windows asset; the CI job
    `setup:clean-clone` runs the launcher on Linux for a merge request that changes `.pre-commit-config.yaml` or
    another path in its `.setup_paths`; a merge request that changes only `scripts/run_gitleaks.py` does not.
  - Hashes are pinned for the release assets of one version; a version bump edits `VERSION`, the hashes and the CI image
    tag together (the version test fails if the tag is left behind).
  - The download needs network access the first time on a machine; a machine without it must fetch the binary by hand.
  - The scan sees what is staged. The full-history scan stays in CI.

regression_checklist:
  - The scan uses the same gitleaks version and `.gitleaks.toml` as before, so what it flags is unchanged.
  - The other hooks, `bootstrap.py --verify` and the CI jobs keep their behaviour.
