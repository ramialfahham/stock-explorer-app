# Review

diff_sha256: 4f783aceae2d1da48b1e4adafa3656e7e3c37d9b4cd29af282ae29e5fed822ae

Four rounds, plus a fifth reviewer added after the commit gate caught an error in this record.
Reviewers: scope-auditor, cto-reviewer, analytics-engineer-reviewer and
equity-analyst-reviewer, all four required by routing for the staged set (`scripts/*` and
`tests/*` -> cto-reviewer; `*.csv` -> analytics-engineer-reviewer; `*metric_catalogue.csv` ->
equity-analyst-reviewer; scope-auditor always). data-engineer-reviewer is NOT required: no
`supabase/*` file is staged.

**This record first claimed analytics-engineer-reviewer was not required, on the reasoning that
the only dbt artifact touched was a seed's copy columns rather than a model or SQL. That was
wrong: the routing rule is `*.csv`, and `dbt_analytics/seeds/metric_catalogue.csv` is staged.
The commit gate rejected the commit and named the missing reviewer.** Recorded because the
failure mode is worth keeping: the reviewer was reasoned out of the routing on the basis of what
the change DID, when the routing is keyed on which FILES it touches. The gate was the only thing
that caught it.

**Reviewer dispatch:** the plugin's reviewer agent types are still not registered as dispatchable
in this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Same role text, same cold blinded input, read-only.

**Final verdicts:** equity-analyst-reviewer PASS (round 3), scope-auditor PASS (round 4),
cto-reviewer PASS (round 4), analytics-engineer-reviewer PASS (round 5, seed only).

**analytics-engineer-reviewer, round 5.** Verified the seed against the staged blobs with two
independent CSV parsers (Python `csv` and DuckDB `read_csv_auto`, the reader `dbt seed` uses):
13 rows plus header, exactly 21 fields on every row under both, no ragged rows, no BOM, no CR
bytes, no newline inside a quoted cell. A per-cell diff against HEAD shows exactly 14 changed
cells across 6 metrics, all confined to `interpretation`/`gloss`/`analogy`/`learn`, with no
`direction`, `applies_to`, `format`, `perspective`, `display_order`, `importance_tier`,
`benchmarkable`, `base_relation`, `numerator_expr` or `denominator_expr` cell moved. That is
the check that matters here, because hand-editing this CSV has silently shifted columns before.
It also traced downstream reach rather than accepting the claim: nothing does
`ref('metric_catalogue')`, no migration references it, and `export_to_supabase.py` exports only
the mart, so "the card face changes on merge with no pipeline run" holds. Three of its five
non-blocking findings were inaccuracies in this branch's own comments and contract, and were
fixed: the currency deny-list comment attributed per-market currencies to
`docs/market_registry.yml`, which has no currency field (the value comes from yfinance
`info_currency` per ticker, so nothing in the repo can enumerate it); `_VISIBLE_COPY_FIELDS`
omitted two exported columns while its docstring claimed to cover what reaches the reader; and
the contract's impact_map said `interpretation` renders on the card face when no frontend module
binds it. Its other two findings are pre-existing and left: seed columns sit outside the dbt doc
gate, and `card_copy.py` keeps a hardcoded analogy override that is a second source of truth the
seed guard structurally cannot see.

## What this branch is

The 2026-08-26 pipeline run was the first time the read prompt was ever sampled at scale, since
there is no `ANTHROPIC_API_KEY` on the dev machine. It exposed two defects, measured across all
921 regenerated reads: 246 (27%) named a currency belonging to another market, and 83 blamed the
health verdict on revenue growth that was positive.

**The root cause was not the wording.** `currency` was passed only to `_format_metric_value`, and
operating and financial cards carry no `currency`-formatted metric at all, so on 918 of 921 cards
the currency never entered the prompt. The model was not disobeying an instruction; it had no
currency and the glosses said "dollar", so it guessed.

## The findings that changed the work

**1. The fix was half a fix, and a reviewer caught it, not the author.** The same "each sales
dollar" framing was live in the CARD FACE copy (`metric_catalogue.csv` across six metrics, a
hardcoded string in `card_copy.py`, and a docs table). Fixing only the prompt would have corrected
the AI paragraph and left the identical defect in the static text beside it, permanently, on every
non-US card. The branch was widened with the owner's approval. **Lesson: when a defect is a phrase,
grep for the phrase across every layer that renders text before scoping the branch, not after.**

**2. Two owner corrections reversed the design, both times correctly.** The first draft BANNED
explaining a margin as an amount per unit sold. The owner rejected that ("actually, this is easy to
understand for beginners"), which reframed the whole defect: the idiom is good teaching, the wrong
currency is the bug. The second: an over-correction claiming "growth that is positive is never a
weakness, however small" was flagged as a false financial universal, since +0.2% is a real-terms
decline. Both times the agent's instinct was to forbid something, and both times the correct answer
was to make it accurate instead.

**3. `net_margin_pct` is bank-only, and the currency fix broke its noun.** `applies_to=financial`.
The old copy said "each revenue dollar", which was the right noun with the wrong currency framing.
The rewrite produced "each sale", fixing the currency and breaking the noun, on a metric whose own
`applicability` field says a bank's revenue is net interest plus fees rather than sales. Caught by
equity-analyst-reviewer. A guard now fails if any financial-only metric's user-visible copy says
"sale". **Lesson: a find-and-replace across shared copy has to be checked per company type, because
`applies_to` decides who actually reads the string.**

**4. `revenue_growth_yoy_pct` is one quarter, not a year.** The first version of the corrected rule
told the model growth "compares this year's sales with the same period a year earlier". It is the
latest reported quarter against the same quarter a year earlier, which both the seed `description`
and its `learn` text say. Unfixed, that would have put annual framing on a quarterly number across
all 921 reads.

**5. The currency label was false twice before it was right.** "Reports in" asserts an accounting
fact the pipeline does not have, because the mart's `currency` is `coalesce(info_currency,
dim_stock.currency)`, a display code, while the real reporting currency `stmt_currency` stops at
`fct_fundamentals_snapshot`. "Currency shown on this card" was then false on operating and
financial cards, which render no money at all: only the three `currency_compact` metrics do and all
three are `pre_revenue`. It now reads "Currency this company trades in", which is what
`info_currency` actually is. **Two independent reviewers had to reject two successive labels before
the true one was found, and each was rejected by tracing the column to its source rather than
reading the wording.**

**6. `GBp` is pence.** 89 of 92 FTSE cards carry it. Every other consumer in the repo upper-cases
before formatting, so the card face already shows a pound sign; passing the raw code would have
named the model a unit appearing nowhere on the card. It was visible in the author's own query
output and walked past; equity-analyst-reviewer caught it.

**7. The author's own bookkeeping was the last thing blocking, twice.** The contract's test
arithmetic was wrong in round 2, corrected wrongly in round 3, and only right in round 4 once it
was MEASURED rather than written from memory between edits. Both blocking findings in round 3 were
of this kind: a handover that still said the `INPUT_HASH_VERSION` bump was unapproved while the
contract recorded the owner's approval, in the same commit. **Lesson recorded in `done_when`:
measure claims about the diff, never estimate them.**

## Escalations and their recorded answers

- **`INPUT_HASH_VERSION` 5a.3 to 5a.4, a §6 cost decision (~921 Haiku calls): APPROVED by the
  owner.** Escalated explicitly rather than assumed. Without it the corrected prompt ships and
  every stored read keeps its defective prose, because the hash covers the metric inputs, the
  verdict and the version, never the prompt text. The card-face half of this branch needs no run
  at all; only the AI paragraph depends on the bump.
- **Widening scope to the card copy: APPROVED by the owner** after the half-fix was surfaced.
- **The exact strings remain §6 owner content** and are proposed, not decided, by the agent.

## Deliberately not fixed, recorded rather than silently skipped

- **Reporting vs trading currency.** A company that files in USD and trades in GBp gets a read
  denominated in pence. Fixing it needs `stmt_currency` plumbed to the mart, an export column and
  a migration. Strictly better than the pre-fix behaviour either way, and the ratio itself is
  currency-invariant.
- **Pre-existing em dashes** in `frontend/card_copy.py` (13) and `docs/ux_principles_finanz_lern_apps.md`
  (15). Two of them, `card_copy.py:261` and `:341`, are the user-visible "no value" placeholder
  glyph, so changing them alters rendered UI and is owner content. This branch introduces none.
- **`supabase/migrations/010_card_assessments.sql`** also states the hash payload and is NOT
  updated: it is applied, the runner tracks by filename with no checksum, so an edit could never
  reach the database and would only make the repo describe a comment differing from the live one.
  Applied migrations are immutable.
- **`revenue_growth_yoy_pct`'s `learn` copy** ("One quarter can be noisy") still argues with a
  badge that now moves on one quarter. That is MR !43's open owner question about the VERDICT, not
  about currency; answering it here would settle an escalation belonging to its own thread.

## Verification

- pytest **245 passed**. `tests/tooling/test_assessment_rules.py`: 32 test functions at HEAD, 49
  now (17 new), 51 collected, **15 of 51 fail against the pre-fix `assessment_rules.py` and
  `metric_catalogue.csv`**; the rest are regression guards that pass both ways by design. The new
  `tests/frontend/test_card_copy.py` guard fails against the pre-fix `card_copy.py`. Both
  independently reproduced by cto-reviewer and scope-auditor in isolated trees.
- `dbt build` **108/108** on `--full-refresh` with a seed reload.
- The five static CI gate scripts green.
- `frontend/metrics.json` byte-identical to a fresh regeneration from the seed. Seed re-parses at
  13 rows x 21 columns with no ragged rows, which is the failure mode hand-editing that CSV
  actually has.
- **Zero em or en dashes on any added line.**
- **UX PR gate** (`docs/working_agreement.md`, required for Streamlit copy): the app was run and
  read at 375px, stricter than the gate's 480px, with no horizontal overflow; every reworded string
  was verified through `frontend/card_copy.py`'s real render path rather than trusting the seed.
  Items 1, 2 and 4 do not apply (copy only, no layout, interaction or tab-behaviour change); item
  3's one-sentence job statement goes in the MR description.

**What is NOT verified, and cannot be here:** the model's OUTPUT under the corrected prompt. There
is no `ANTHROPIC_API_KEY` on this machine, so the prompt is proven correct and the prose is not.
That only proves out on the next pipeline run. It is the same blind spot that let the original
defect ship, and it is unchanged by this branch.

## Post-PASS edits

After both round-4 PASS verdicts, four NON-BLOCKING findings the reviewers themselves recommended
were applied: the `_CURRENCY_WORDS` comment claimed five markets when the registry lists nine (four
dormant, one of them CHF) and named a trigger that misses activation-by-flag; `ebit_margin_pct`'s
`learn` and the docs table kept a per-sale framing the prompt now forbids; `docs/data_contract.md:384`
still described the hash payload without the currency; and `card_copy.py`'s hardcoded analogy
overrides had no guard. `tests/frontend/test_card_copy.py` was added to `scope_paths` by amendment
for the last of these. A fifth round then fixed three more, all of them inaccurate claims this
branch made about itself rather than defects in the shipped behaviour. No design decision
changed at any point; the `diff_sha256` above is the final state.

## Process note worth keeping

`git stash` was used mid-review to measure pre-fix failures and silently unstaged two files. The
content was identical and the hash check caught it, but it briefly invalidated a running review.
**Measure against `HEAD` in a temp tree instead; never move the index while a reviewer is reading
the staged diff.** Round 2 also had two reviewers reporting against a snapshot the working tree had
already moved past, which cost a round of confusion about which findings were live.

## scope-auditor

Rounds 1, 2, 3, 4. Round 1 FAIL (6 blocking), round 2 FAIL (5 blocking), round 3 FAIL
(3 blocking), round 4 PASS.

Its blocking findings drove most of this branch's shape. Round 1: the contract's `done_when`
required the prompt to FORBID the per-unit currency idiom while the shipped rule ENCOURAGED it,
in the same diff; the currency line was an undeclared new prompt input; a null currency left the
prompt pointing at a currency it had not supplied; dated changelog narrative had been
reintroduced into test comments, one commit after the owner ruled on exactly that; and
`metric_catalogue.csv` still shipped "each dollar of sales" to the reader, which is what forced
the branch to be widened. Round 3: the handover still said the `INPUT_HASH_VERSION` bump was
unapproved while the contract recorded the owner's approval, in the same commit; the test
arithmetic was wrong on all three numbers; and the "repo-wide sweep is clean" clause was false
because of deliberate quotations it did not exempt. Round 4 verified every number by
measurement in an isolated pre-fix tree, confirmed all 11 staged paths sit inside `scope_paths`,
and confirmed no owner-level decision was taken silently.

VERDICT: PASS

## cto-reviewer

Rounds 1, 2, 3, 4. Round 1 FAIL (4 blocking), round 2 FAIL (4 blocking), round 3 FAIL
(2 blocking), round 4 PASS.

Found that the prompt rule mis-framed returns and growth as amounts per unit of sales, wrong for
ROE (per equity), ROA (per assets) and growth (versus the prior-year period), and worst on
financial cards where three of four fields are affected; that the rule failed open when
`currency` was null; that the gloss guard substring-matched "cent" inside "percent"; that
`compute_input_hash` excluded `currency` even though the prompt named it; that "Reports in" and
then "Currency shown on this card" both asserted things the pipeline cannot support; that a NaN
currency raised `AttributeError` on `.strip()`; and that the shared prompt hard-coded "17 yen"
and "24 cents", reintroducing the very pressure the branch exists to remove. Round 4 rebuilt the
pre-fix state in an isolated tree and reproduced 15 failures of 51 collected, confirmed
`metrics.json` byte-identical to a regeneration, and confirmed no new dependency, CI step, hook,
secret or permission.

VERDICT: PASS

## analytics-engineer-reviewer

Round 5, seed only. Required by routing (`*.csv`) and initially, wrongly, reasoned out of the
routing by this record; the commit gate caught that.

Verified the staged seed with two independent CSV parsers including DuckDB's, the reader
`dbt seed` actually uses: 13 rows plus header, exactly 21 fields on every row under both, no
ragged rows, no BOM, no stray CR, no newline inside a quoted cell. A per-cell diff against HEAD
isolates exactly 14 changed cells across 6 metrics, all in `interpretation`/`gloss`/`analogy`/
`learn`, with every taxonomy and expression column byte-identical. That is the check that
matters, because hand-editing this CSV has silently shifted columns before. Traced downstream
reach rather than accepting it: nothing does `ref('metric_catalogue')`, no migration references
it, `export_to_supabase.py` exports only the mart, so the impact_map's "card face changes on
merge, no pipeline run" holds. Confirmed the `assessment_rules.py` mirror cannot have drifted
since no `applies_to` or `direction` cell moved, and that the new guards are non-vacuous by
replaying their predicate against the HEAD seed, which flags precisely the 14 changed cells.
Three non-blocking findings were inaccurate claims this branch made about itself and were fixed;
two are pre-existing and recorded above.

VERDICT: PASS

## equity-analyst-reviewer

Rounds 1, 2, 3. Round 1 FAIL (4 blocking), round 2 FAIL (5 blocking), round 3 PASS.

The financial correctness of this branch rests on its findings. It caught that `GBp` means
pence and that 89 FTSE cards carry it; that the growth and returns denominators were wrong; that
"growth that is positive is never a weakness, however small" asserts a false universal, since
+0.2% is a real-terms decline and teaching a beginner otherwise mirrors the defect being fixed;
that `net_margin_pct` renders only on bank cards, so replacing "each revenue dollar" with "each
sale" fixed the currency and broke the noun on a metric whose own applicability field says a
bank's revenue is net interest plus fees; that "per unit sold" describes profit per item, a
number the model has no volume data for; and that `revenue_growth_yoy_pct` is one quarter rather
than a year. In round 3 it re-derived every check from the seed rather than the diff, including
scanning all 21 fields of both financial-only rows, and confirmed the prompt carries no advice,
no valuation claim, no invented threshold and no named currency.

VERDICT: PASS
