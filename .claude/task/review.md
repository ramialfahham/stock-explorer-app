# Review

diff_sha256: aebd822c933eff7a137c6fcc647cb6fb1f7a08254cb0b8d3a11f6bdfc5c85abc

## scope-auditor
VERDICT: PASS
risks_checked:
- All staged paths inside scope_paths (.pre-commit-config.yaml, .claude/**). No out-of-scope edit.
- Single intended change: gitleaks hook entry `gitleaks protect …` → `gitleaks git --pre-commit --staged --redact --config .gitleaks.toml`. Same scan semantics (staged secret scan), same config, just the non-deprecated subcommand. No other hook, version, path, or stage touched.
- Verified, not asserted: `gitleaks git --pre-commit --staged --redact --config .gitleaks.toml` runs on gitleaks 8.30.1, loads the config, and exits 0 ("no leaks found"); flags confirmed via `gitleaks git --help`.
- impact_map "(none)" holds: pre-commit config only — no runtime, dbt, ingestion, or CI behavior change.
