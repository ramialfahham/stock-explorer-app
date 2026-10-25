# Review

diff_sha256: 85ecb89ffc92e380e5122adc2fb66f20a7035ff20130550a127664d277db415d
rounds: 2

Works #72 defects 10 to 13 (items 14, 16, 18, 19 are owner calls, untouched). Round 1 (tree 7b74742):
analytics-engineer-reviewer PASS, platform-reviewer PASS, equity-analyst-reviewer PASS, scope-auditor FAIL on two
design findings: the Reuse text in `docs/layering.md` and the section 1.2 text were my wording, not the owner's
chosen words (an added "from several sources", an added two-line cap). Fixed in round 2 (tree 2968c2a): the Reuse
condition uses the owner's "single-consumer entity table", section 1.2 reads "One sentence per comment, which may
wrap onto more than one line", the grain lines say "each at its latest snapshot_date", the Used-by check's comment
is one sentence and its message lists the extra and the missing names. Round 2: scope-auditor, platform-reviewer
and analytics-engineer-reviewer all PASS (the equity analyst's file did not change). After the PASS verdicts only
the "This machine" note in `.claude/active_work.md` changed (the secret scan now runs through
`scripts/run_gitleaks.py`, merged in !268).

Coordinator evidence:
- Before the rebase onto main: `bootstrap.py --verify` steps run one by one: sqlfluff lint clean, dbt build 149
  tests pass including the 29 unit tests with the changed `dim_stock` inputs. After it: pytest 1468 passed,
  1 skipped; the commit runs every hook, including the secret scan.
- The real-fixture replay built through dbt: `check_real_fixture_mart.py` reports 73 rows match the golden file;
  `tests/fixtures/real/golden_mart.csv` is unchanged.
- `dbt docs generate` then `scripts/check_dbt_documentation.py` passes, including the new Used-by check; with the
  two old wrong lines restored in memory it reports exactly those two models.
- Mutations of the Used-by check, file restored after each, seven in all: mismatch never reported, only extras,
  only missing, other packages not ignored, substring name match, model without the line not skipped, check not
  called from `main()`. Each fails a test.
- The scan for two-line comment blocks with two full sentences in `dbt_analytics/` finds none; em-dash,
  narrative-date and context-budget checks pass.

follow_ups (owner questions for the merge request): `docs/layering.md` line 68 ("shared across multiple use
cases") and lines 87-88 ("attribute masquerading as entity") sit beside the amended condition 2: amend them or
leave them; the Used-by line is skipped for core, intermediate and mart models that lack it: require it or say
it is optional in `docs/engineering_standards.md` section 2; a mismatch message prints an empty bracket pair when
only one side differs (cosmetic).

## scope-auditor

VERDICT: PASS
reviewed_tree: 2968c2a7cc7701e9b98c4bd215bb25c0c37ba7af
risks_checked:
- The Reuse and section 1.2 wording matches the owner's recorded answers; the delta stays inside `scope_paths`.
- Owner-call items 14, 16, 18, 19 are untouched; no changed claim is left standing.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 2968c2a7cc7701e9b98c4bd215bb25c0c37ba7af
risks_checked:
- The Used-by check's message names the extra and the missing models; its comment and docstring are true.
- The exact-message assertions are confined to the two tests that pin the message.
wording_fixes: none required.

## analytics-engineer-reviewer

VERDICT: PASS
reviewed_tree: 2968c2a7cc7701e9b98c4bd215bb25c0c37ba7af
risks_checked:
- The grain lines are true against `fct_fundamentals_snapshot` and the data contract.
- No SQL changed in round 2; every Used-by line matches the real `ref()` dependencies.
wording_fixes: none.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 7b747421c5a88f109d90db324be84bb47be0e2f5
risks_checked:
- The company-type rule is unchanged in effect: `dim_stock`'s sector was always the same row's `info_sector`.
- The grain sentence in the data contract is true; no metric definition or card number changed.
wording_fixes: none.
