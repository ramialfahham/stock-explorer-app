# Task contract

objective: **Slice 5b — AI assessment: the Claude-written prose "read" (regenerate-on-change).** Second half
  of Slice 5. For each `card_assessments` row, **Claude Haiku** writes a 2–3 sentence beginner "read" of what
  the card's numbers say, ending on the verdict's meaning ("financially sturdy on these figures", never "a good
  buy"). Fills `ai_read` + `read_model` (null since 5a). The generator calls Claude **only when the card's
  `input_hash` changed or its stored `ai_read` is null** — the whole cost story. Adds the `anthropic` dep +
  `ANTHROPIC_API_KEY` secret; the CI dry-run smoke stays **secret-free** (no LLM call). Still data-only (Slice 6
  renders). Approved plan: ~/.claude/plans/functional-zooming-quasar.md (supersedes the 5a plan; the plan file
  itself was lost in the session crash — its contents are captured in `decisions_reserved`/`technical_definition`
  below).

scope_paths:
  - scripts/assessment_rules.py                    # + READ_SYSTEM_PROMPT / READ_METRIC_BRIEF / build_read_messages (pure)
  - scripts/generate_assessments.py                # + Haiku call + regenerate-on-change gate (attach_reads)
  - requirements.txt                               # + anthropic==0.116.0 (exact pin)
  - .env.example                                   # + ANTHROPIC_API_KEY (documented)
  - docs/data_contract.md                          # card_assessments read now populated (factual)
  - tests/tooling/test_assessment_rules.py         # + build_read_messages + READ_METRIC_BRIEF coverage guard
  - tests/tooling/test_generate_assessments.py     # + attach_reads (regen/carry/fail) + no-key/with-key main
  - .gitignore                                     # pending housekeeping fold-in (ignores settings.local.json / dev.duckdb)
  - tests/tooling/test_export_to_supabase.py       # unrelated 2-line fix, disclosed below — not this slice's content
  - .claude/task/contract.md

review_artifacts (separate artifact-only commit after; review.md records the reviewed diff's hash):
  - .claude/task/review.md
  - .claude/active_work.md                          # incl. the 5a PR'd -> MERGED (#148) flip + 5b advance

decisions_reserved (owner-approved this session; §6 — plan-approved):
  - **Rules decide the verdict color** (5a); the **LLM writes ONLY the prose read.** Model = **Claude Haiku**
    (`claude-haiku-4-5`); **regenerate only when `input_hash` changes or `ai_read` is null** (a prompt/model
    change needs an `INPUT_HASH_VERSION` bump to refresh globally).
  - **Read voice (owner-signed system prompt + per-type sample reads):** educational, **NEVER advice**;
    true-beginner language; **reason only from the given numbers**; per-type lens (operating / financial (bank,
    with the profitability-only honest limit) / pre_revenue survival); ends on the verdict's meaning as financial
    sturdiness/strain "on these figures". **Valuation (P/E, P/TBV) and growth are fed as context only** — never a
    buy cue.
  - **Facts fed to Claude = `INPUT_FIELDS_BY_TYPE`** (the same per-type set the hash covers).

technical_definition:
  - **assessment_rules.py (pure, no I/O, no anthropic import):** `READ_SYSTEM_PROMPT` (the voice) + `VERDICT_MEANING`
    + `READ_METRIC_BRIEF` (label + plain gloss + value format per metric; MUST cover every `INPUT_FIELDS_BY_TYPE`
    field — a `tests/tooling` guard asserts it; valuation/growth/income tagged "context only"); `build_read_messages(row,
    verdict) -> (system, user)` renders one line per **present** per-type metric (missing omitted, never guessed).
  - **generate_assessments.py:** `import anthropic`; `READ_MODEL="claude-haiku-4-5"`, `READ_MAX_TOKENS=256`.
    `_fetch_existing_assessments(client)` selects `input_hash`/`ai_read`/`read_model` per `(market_code, ticker)`.
    `_generate_read(client, row, verdict)` calls Haiku, returns `(text, model)` or `(None, None)` on any error
    (one bad card never fails the batch). `attach_reads(records, rows_by_key, existing_by_key, client)` (client
    injected) regenerates iff new / hash changed / stored `ai_read` empty, else leaves `ai_read`/`read_model`
    **absent** so the upsert preserves the stored read (never clobbers). `main` real path gates the entire read
    step on `ANTHROPIC_API_KEY` (verdicts-only when absent); `--dry-run` still returns **before** any client/key.
    `build_assessment_records` is unchanged (5a's key-set assertion stays green — reads attach in a later step).
  - **requirements.txt:** `anthropic==0.116.0` (exact pin, repo convention).
  - **Pipeline (adapted mid-flight — CI moved to GitLab while this slice was parked):** no `.gitlab-ci.yml`
    change at all. GitLab injects every project CI/CD variable into every job (no per-step `env:` mapping the
    way GitHub Actions needed), and `generate_assessments.py` reads `ANTHROPIC_API_KEY` via `os.getenv` — the
    `data-pipeline` job's existing `python scripts/generate_assessments.py --duckdb-path storage/stock_data.db`
    call picks it up automatically once the variable exists. Only action needed: add `ANTHROPIC_API_KEY` as a
    **Protected** CI/CD variable at the project level (protected branch pipelines only, same as the Supabase
    credentials) — owner-only, project settings, not a repo-content change. `validate:full`'s existing dry-run
    smoke (`generate_assessments.py --dry-run`) is already secret-free; unaffected by this slice.
  - **No migration change** (010 already has `ai_read`/`read_model`).

done_when:
  - `pytest tests/` green incl. `build_read_messages` per type (facts present, verdict stated, valuation/growth
    tagged context-only, missing omitted) + the `READ_METRIC_BRIEF` coverage guard + `attach_reads`
    (regenerate / carry-forward / stored-null-regenerate / per-card-failure isolation) + `main` no-key (verdicts
    only) and with-key (reads attached) paths. 5a's `test_build_records_*` / `test_dry_run_needs_no_credentials`
    still pass unchanged.
  - `python scripts/generate_assessments.py --duckdb-path storage/stock_data.db --dry-run` prints one verdict per
    eligible card, **no LLM call, no creds**.
  - `data_contract.md` §card_assessments accurate; `anthropic` pinned; **CI smoke stays secret-free; no new
    migration, no dbt/mart/frontend change.**
  - Full blinded review recorded in `review.md`; reviewed commit + separate artifact commit; MR to main (NOT merged).

impact_map:
  - New `anthropic` dependency. Fills `ai_read`/`read_model` on `card_assessments` via Claude Haiku,
    regenerate-on-change. **Data-only** (Slice 6 renders). No dbt / mart / frontend / migration change.
    `ANTHROPIC_API_KEY` is a new project-level CI/CD variable (owner sets it; not a repo-content change).
  - Required reviewers (per `.claude/review_routing.json`): **scope-auditor** (always) · **cto-reviewer**
    (`scripts/*` · `tests/*` · `.gitlab-ci.yml` · `requirements*.txt`) · **equity-analyst-reviewer**
    (`docs/data_contract.md` + the read voice). **NOT** analytics-engineer / data-engineer — 5b touches no
    `*.sql` / `*.csv` / dbt-yml / `supabase/*` / `ingestion/*`. Owner approved running the **3 routed reviewers**.

amendments:
  - 2026-07-11 — Slice 5b per approved plan functional-zooming-quasar.md (supersedes the 5a plan
    dynamic-snuggling-truffle.md; owner approved the plan incl. the read-voice system prompt + per-type sample
    reads, the valuation/growth "context only" guard, the Claude Haiku + regenerate-on-change gate, and the
    3-reviewer routing).
  - 2026-08-16 — Resumed after a session crash lost the working chat (code + tests were already complete and
    passing; only the review cycle was outstanding) and after two intervening infra changes landed on `main`:
    the GitHub->GitLab CI migration and `--target dev` Supabase isolation. Pipeline references in
    `scope_paths`/`technical_definition` updated from the now-deleted `.github/workflows/*.yml` to
    `.gitlab-ci.yml`; no change to this slice's own product/technical decisions.
  - 2026-08-16 — `tests/tooling/test_export_to_supabase.py` added to scope_paths: a 2-line fix, unrelated to
    this slice's content. `test_dry_run_needs_no_credentials_regardless_of_target` (written for the
    already-merged `--target dev` task) called `monkeypatch.delenv` on Supabase credentials, but
    `export_to_supabase.main()` calls `load_dotenv()` internally, which silently re-populated them from this
    machine's real local `.env` — the test only worked in environments with no `.env` file (CI, throwaway
    worktrees) and was environment-dependent everywhere else. Discovered while running the full suite to
    verify this slice's resumption. Fix: stub `load_dotenv` to a no-op in that one test.
  - 2026-08-16 — cto-reviewer pass 1 FAIL, both findings fixed and reviewer-confirmed on pass 2: (1) the same
    `load_dotenv()`-vs-`monkeypatch.delenv` leak also existed in
    `test_generate_assessments.py::test_main_without_anthropic_key_upserts_verdicts_only` (deleted
    `ANTHROPIC_API_KEY` without stubbing `load_dotenv`, so a real local `.env` could push the test onto a
    live, credentialed network call to api.anthropic.com inside what must be an offline unit test) — same
    fix applied; (2) `.env.example` said "ANTHROPIC_API_KEY GitHub Actions secret", stale since the CI
    migration — corrected to "Protected GitLab CI/CD variable".
  - 2026-08-16 — equity-analyst-reviewer pass 1 FAIL: `READ_METRIC_BRIEF["debt_to_equity"]` /
    `["statement_roe_pct"]` glossed direction with no caveat for negative/thin shareholders' equity, though
    `metric_catalogue.csv`'s own `applicability` text for both rows documents exactly this distortion and the
    dbt guard only excludes exact-zero equity, not negative — a live, reachable case. **Owner-approved
    (2026-08-16, in-session):** add a caveat to both glosses, reusing the catalogue's own wording verbatim
    rather than inventing new text. `debt_to_equity` gains "distorted or meaningless if equity is thin or
    negative"; `statement_roe_pct` gains "can look spuriously positive if equity is negative".
  - 2026-08-16 — equity-analyst-reviewer pass 2 FAIL (fresh full pass after pass-1 fixes verified genuine):
    three more instances of the same missing-caveat pattern, plus one different framing defect.
    **Owner-approved (2026-08-16, in-session):**
    - `forward_pe` gloss: add "meaningless (not \"cheap\") if the company is a loss-maker" (from the
      catalogue's "Undefined for loss-makers... the value is meaningless, not 'cheap.'").
    - `net_debt_to_ebitda` gloss: add "can explode to a huge or distorted number when earnings are near
      zero" (from the catalogue's "explodes when EBITDA ≈ 0").
    - `revenue_growth_yoy_pct` gloss: add "a huge percentage can just mean a very small prior-year base, not
      real momentum" (from the catalogue's "Distorted by tiny prior-year bases... huge % off a small base").
    - `READ_SYSTEM_PROMPT`'s company-type lens hardcoded every `company_type == "financial"` card as "the
      bank" and warned about "the bank's safety or capital strength" — but `financial` covers the whole GICS
      "Financial Services" sector (insurers, asset managers, brokerages, exchanges too), and nothing else in
      `data_contract.md`/`north_star.md` uses "bank" as shorthand for the category, so this was a narrow
      oversight in this one prompt, not an established simplification. Generalized to "this financial
      company" / "company's balance-sheet safety or capital strength" — same honest-limit meaning, not
      falsely bank-specific.
  - 2026-08-17 — equity-analyst-reviewer pass 3 FAIL: three more confirmed instances of the missing-caveat
    pattern, plus a PLAUSIBLE (lower-confidence) one. Rather than wait for a fourth review round, did a full
    manual cross-check of all 16 `READ_METRIC_BRIEF` fields against their `metric_catalogue.csv`
    applicability rows. **Owner-approved (2026-08-17, in-session) — exact final gloss text, verbatim:**
    - `net_margin_pct`: `"final profit kept from each revenue dollar after all costs (higher = more
      profitable); for a financial company \"revenue\" means net interest plus fees, not sales"` (was "sales
      dollar" — wrong, since this field is financial-only and a bank/insurer's revenue isn't sales; traces
      to the catalogue's "For a bank, 'revenue' is net interest plus fees").
    - `dividend_yield_pct`: `"annual dividend as a share of the price - income context, not a health signal;
      a very high yield can flag a falling price or a payout at risk, not just generosity"` (catalogue-
      verbatim on the added clause).
    - `current_ratio_stmt`: `"short-term assets versus short-term bills (above 1 = covers near-term bills);
      a very high ratio isn't automatically good either - it can mean cash sitting idle"` (catalogue-
      verbatim on the added clause).
    - `ebit_margin_pct`: `"share of each sales dollar kept as operating profit (higher = more profitable);
      can look extreme when revenue is very small"` — **adapted, not a catalogue quote**, disclosed as such
      when proposed. A low-but-positive-revenue operating company can still produce an exploded percentage;
      the catalogue's own "breaks for pre-revenue firms" framing doesn't quite fit since pre_revenue-type
      cards never receive this field at all (a narrower, different case the catalogue wasn't written for).
    - `fcf_margin_pct`: `"real cash kept from each sales dollar (higher = stronger); negative = burning
      cash; can look extreme when revenue is very small"` — same adaptation and same disclosure as above.

    Every other field checked against its catalogue row and found already adequate (either the distortion
    case isn't reachable given `company_type` boundaries — e.g. `debt_to_equity`'s "not shown for banks" —
    or the caveat is soft/methodological rather than a hard
    reachable distortion, e.g. `roa_pct`'s period-end-vs-averaged-assets note).
