# Review — Slice 5b: AI assessment — Claude Haiku prose read (regenerate-on-change)

diff_sha256: 37648ddf0230841c112502729d3e815b1e7e360f2e355e8d6d097f3b796a0252

**Change under review (11 files):** the second half of the AI assessment generator — a 2-3
sentence Claude Haiku prose "read" per card, reasoning only from that card's own numbers,
ending on the verdict's meaning, never a buy/sell cue. Regenerated only when a card's
`input_hash` changes or its stored `ai_read` is null. Fills `ai_read`/`read_model`
(previously null since 5a). Adds the `anthropic` dependency; no migration, dbt, mart, or
frontend change. Resumed after a session crash lost the working chat mid-review-cycle; code
and tests were already complete, only review was outstanding.

**Outcome: all three PASS after five review rounds** (four real, substantive rounds of
findings — not process noise). Local verification: `pytest tests/` 142 passed, and the
generator dry-run over the real mart yields a verdict per eligible card (35 cards), no
credentials required.

## What the five rounds actually found and fixed

1. **scope-auditor FAIL (round 1)** — the caveat-wording additions below were owner-approved
   in-session but not recorded as a contract amendment. Fixed: amendments added.
2. **cto-reviewer FAIL (round 1)** — `test_main_without_anthropic_key_upserts_verdicts_only`
   deleted `ANTHROPIC_API_KEY` via `monkeypatch.delenv` without stubbing `load_dotenv`, so a
   real local `.env` could silently push the test onto a live, credentialed network call to
   `api.anthropic.com` inside what must be an offline unit test. `.env.example` also had a
   stale "GitHub Actions secret" reference, left over from before the GitLab migration. Both
   fixed and reviewer-confirmed on round 2.
3. **equity-analyst-reviewer FAIL (rounds 1–3)** — `READ_METRIC_BRIEF` glosses fed to Claude
   were missing applicability caveats that `metric_catalogue.csv` itself already documents as
   owner-approved: negative/thin equity (`debt_to_equity`, `statement_roe_pct`), loss-makers
   (`forward_pe`), near-zero EBITDA (`net_debt_to_ebitda`), tiny prior-year bases
   (`revenue_growth_yoy_pct`), a "financial = bank" mislabeling in `READ_SYSTEM_PROMPT` that
   misdescribed insurers/brokers/asset managers, wrong "sales dollar" framing for the
   financial-only `net_margin_pct`, and missing distress/idle-cash caveats on
   `dividend_yield_pct`/`current_ratio_stmt`. Rather than wait for further rounds, did a full
   manual cross-check of all 16 `READ_METRIC_BRIEF` fields against their catalogue rows;
   found and fixed two more (near-zero-revenue distortion on `ebit_margin_pct`/
   `fcf_margin_pct` — disclosed as an adaptation, not a catalogue quote, since the catalogue's
   own framing didn't quite fit the reachable case). All 11 additions owner-approved
   in-session; exact final wording quoted verbatim in `contract.md`'s amendments log.
4. **scope-auditor FAIL (round 4)** — the round-3 amendment used a vague back-reference
   ("the 3 catalogue-verbatim additions above") instead of quoting exact approved text,
   so it couldn't be mechanically verified against the code — even though the content itself
   was already independently confirmed correct by the other two reviewers that same round.
   Fixed: rewrote the amendment to quote every final string verbatim, in backticks.

Round 5 confirmed all of the above holds character-for-character against the live code.

## scope-auditor
VERDICT: PASS
risks_checked:
- All five round-4 gloss strings (`net_margin_pct`, `dividend_yield_pct`, `current_ratio_stmt`,
  `ebit_margin_pct`, `fcf_margin_pct`) verified character-for-character identical between the
  rewritten contract.md amendment and the live `scripts/assessment_rules.py`.
- Import purity: `assessment_rules.py` has zero `anthropic` imports (pure, offline-testable);
  the LLM call lives only in `generate_assessments.py`, matching the contract's technical
  boundary.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Confirmed via the patch that this round's diff touches only `.claude/task/contract.md` —
  no `.py`, `.yml`, or test file changed since the round-4 PASS.
- Dependency/CI/credential surface unchanged and already verified clean: exactly the
  contracted files touched across all rounds, `requirements.txt` gained only the one
  `anthropic==0.116.0` pin, no `.gitlab-ci.yml`/hook/workflow touched, `--dry-run` provably
  returns before any credential access, `ANTHROPIC_API_KEY` read only via `os.getenv`.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- All eleven owner-approved gloss/prompt strings (rounds 1–4) verified verbatim against the
  live file, including the ones from earlier rounds, not just this round's five — none
  reverted or drifted.
- A full exhaustive pass over all 16 `READ_METRIC_BRIEF` fields and the complete
  `READ_SYSTEM_PROMPT` (round 4) found nothing further blocking; `price_to_tangible_book`'s
  zero/negative-tangible-book distortion confirmed structurally unreachable (nulled upstream
  in dbt, verified against the model's own unit-test fixture) rather than a missed caveat.
