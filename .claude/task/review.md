# Review

diff_sha256: 2565664b064e1e3fd2a5c55419fdb9277a3468aba4b35d46ddf684ca0993ab1e
rounds: 2

Replaces the pre-commit-compiled `gitleaks` hook with `scripts/run_gitleaks.py`, which runs the official release
`v8.30.1`, downloaded once, checked against a pinned SHA-256 and extracted alone. Round 1 (tree 55267b8):
platform-reviewer PASS, scope-auditor FAIL on one point: the done_when grep for the version string also matched
hard-coded asset names in the test fixtures. Fixed in round 2 (tree f21839d): the fixtures build their names from
`rg.VERSION`, and the contract names the files the grep covers. Round 2: scope-auditor and platform-reviewer PASS.
Applied after the PASS verdicts, no round 3: the contract states which merge requests trigger `setup:clean-clone`,
the stubbed fail-closed test is renamed for what it covers, and two tests cover a real archive without the binary.

Coordinator evidence:
- Diagnosis on the owner's machine: the pre-commit copy is a 25 MB unsigned `gitleaks.exe` compiled locally;
  Smart App Control is in enforce mode and refuses it (`WinError 4551`). The official release started, its SHA-256
  matched the published checksum file, and it found no leaks in the staged change of the waiting dbt branch.
- The launcher run for real: downloaded, hash verified by the code, no leaks on the staged change (exit 0);
  exit 1 with rule `gitlab-pat` on a staged fake token (the test file was removed afterwards).
- Mutations of the launcher, file restored after each, nine in all: hash not checked, cache ignored, scan exit code
  lost, error not failing closed, download error not wrapped, `--staged` dropped, `--config` dropped, partial
  file left behind, wrong working directory. Each fails a test.
- `pytest tests` 1459 passed, 1 skipped (the POSIX executable-bit test, on Windows); every pre-commit hook
  passes, including `gitleaks` through the launcher; em-dash, narrative-date and context-budget checks pass.

follow_ups (filed as an issue): the launcher docstring and the config comment keep the reason Smart App Control
needs the launcher while three other files lost it: pick one rule on why-not clauses; the download-failure message
should name the cache folder for a machine without network; whether a cached binary is re-hashed on every run;
add `scripts/run_gitleaks.py` to the paths that trigger `setup:clean-clone`; the Linux and macOS archive layout is
assumed from the Windows asset until the CI job runs it.

## scope-auditor

VERDICT: PASS
reviewed_tree: f21839d5457a519d1556bab6194ee413552186df
risks_checked:
- The version string appears only in the launcher and the CI image tag in the files the grep covers.
- The delta stays inside `scope_paths`; the `.gitlab-ci.yml` change is a comment; the declared known limits are honest.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: f21839d5457a519d1556bab6194ee413552186df
risks_checked:
- The hash is checked before extraction; the per-process temp name cannot leave a partial binary that a later run trusts.
- The new tests pin what they claim; every error path of the launcher exits non-zero.
wording_fixes: applied.
