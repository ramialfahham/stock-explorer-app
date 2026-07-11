# Review — Slice 5a: AI assessment — deterministic health verdict + storage (no LLM)

diff_sha256: 74e3016fa6d6d7010bfc9c3520afd1def0ba36a4e2bd30285d7b0e22de05f745

**Change under review (9 files):** the first half of the AI assessment generator — a deterministic
per-type 🟢/🟡/🔴 **financial-health** verdict (rules decide the color; the LLM is deferred to 5b),
computed from each card's own numbers and stored to a new Supabase table `card_assessments` with an
`input_hash` for 5b's regenerate-on-change. Wires the generator into the weekly pipeline + a no-secret
CI dry-run smoke. Ships **no LLM, no `anthropic` dependency, no API key, no cost**; data-only (Slice 6 renders).

**Required reviewers** (per `.claude/review_routing.json`): scope-auditor (always); analytics-engineer
(`010_*.sql`); data-engineer (`supabase/*`); cto (`scripts/*`/`tests/*`/`.github/workflows/*`);
equity-analyst (`docs/data_contract.md` + the verdict rubric).

**Outcome: all five PASS, single cycle, no blocking findings.** Local verification: `pytest tests/` 117
passed (22 new), and the generator dry-run over the fixture mart yields a verdict per card (35 cards),
no credentials required. Every reviewer independently confirmed 5a ships no LLM/dependency/secret, the
verdict is health-only (excludes valuation + growth), the catalogue mirror holds across all 16 metrics,
the migration is additive/idempotent, and the upsert provably can't clobber a future 5b read.

## scope-auditor
VERDICT: PASS
risks_checked:
- 9 staged files == contract `scope_paths`; the unrelated `.gitignore` change is unstaged/absent from the diff; patch sha256 matches.
- No `anthropic` dep / `ANTHROPIC_API_KEY` / Claude call; `ai_read`/`read_model` are nullable columns omitted from the upsert (null in 5a).
- All §6 decisions (per-type rubric, health-only framing, `(market_code, ticker)` grain, `green|yellow|red` token, generate-and-store, 5a/5b split) recorded in `decisions_reserved` + the 2026-07-11 amendment.
- 5b (LLM read) and Slice 6 (rendering) deferrals documented; review artifacts correctly excluded from this diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Migration 010: FK to `markets`, `health_verdict` CHECK in (green,yellow,red), `input_hash`/`snapshot_date` NOT NULL, `unique(market_code,ticker)` backing `on_conflict`, two indexes, RLS + public select; additive/idempotent (`create table if not exists`), sequential, auto-discovered.
- `INPUT_FIELDS_BY_TYPE` + `DIRECTION_BY_METRIC` reproduce `metric_catalogue.csv` `applies_to`/`direction` exactly (all 16 metrics); the two mirror-guard tests are full set/dict-equality checks against the live seed.
- Verdict logic reads only the health subset (excludes forward_pe/price_to_tangible_book/growth); banding respects the catalogue direction; null handling is total (all-unknown -> yellow); `input_hash` covers the full per-type set + version.
- No dbt model/mart change; all generator SELECT columns exist in `mart_stock_cards`.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `assessment_rules.py` pure (hashlib/json/math only); `compute_verdict` total (null/unknown company_type -> operating; all-unknown -> yellow); `compute_input_hash` float-canonicalized (6dp, NaN->None), order-independent, versioned.
- `generate_assessments.py` mirrors `export_to_supabase`; `build_assessment_records` pure; `--dry-run` returns before the creds check (secret-free CI smoke); upsert omits `ai_read`/`read_model`; `ASSESSMENT_INPUT_COLUMNS` derived from the rules module (can't drift).
- Tests genuinely exercise real code (ran 22 passed): per-type verdicts, boundaries, null-tolerance, totality grid, hash determinism/float-stability/version-sensitivity, catalogue mirror, offline generator (synthetic DuckDB, dedupe, `ai_read` absent, dry-run rc 0 env-stripped, missing-db rc 1).
- Workflows: generate step after export inheriting existing secrets; no-secret dry-run smoke; no new dependency, secret, or LLM call (`requirements.txt` untouched; imports pre-existing).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Migration 010 applies additively ahead of the generator (migrations step precedes it); FK/CHECK/grain/indexes/RLS mirror the mart convention; auto-discovered; `create table if not exists` deliberately non-destructive (preserves a future 5b `ai_read`).
- Non-clobber invariant: `build_assessment_records` emits a uniform 7-key payload omitting `ai_read`/`read_model`, so PostgREST `ON CONFLICT DO UPDATE SET` leaves an existing 5b read untouched; asserted by the offline test.
- Read/coerce/dedupe: read-only mart read, NaN->None, latest-snapshot per `(market_code, ticker)` via ISO-string compare; all 16 metric columns exist in the mart.
- Empty-mart keeps the snapshot (never deletes); `--dry-run` returns before creds; pipeline reuses the service-role secret (no new secret); `data_contract.md` `card_assessments` section factually consistent with the migration + write path.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Health-not-investment-quality: the three verdict functions read only resilience axes; no path reads `forward_pe`/`price_to_tangible_book`/`revenue_growth`/`dividend_yield` (those are hashed for 5b but never scored) — no "cheap P/E -> green".
- Per-type bands defensible + beginner-honest; edge handling correct (negative net-cash -> red; null runway = not-burning -> good with net-cash/WC still gating; missing inputs = unknown, never faked); worst-axis-wins + totality confirmed.
- Bank honest-limit (profitability-only; CET1/Tier 1 unsourceable) stated in `data_contract.md` + a code comment; verdict stays modest. No advice language anywhere; `data_contract.md` factual; owner sign-off of the rubric recorded.
- Non-blocking methodology notes (no change required): (1) a negative `net_debt_to_ebitda` is classed "good", but negative-EBITDA distress is caught independently by the margin axis under worst-axis-wins; (2) financial-green treats a known-mediocre ROA more strictly than an unknown ROA — a defensible "don't penalize missing data" asymmetry.
