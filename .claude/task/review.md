# Review

diff_sha256: 810ec7106e9809de877cf88dce77ae08c9c5a79bde0f90b566b79f73c69bf4e1

Five reviewers, required by routing: scope-auditor (`always`), analytics-engineer-reviewer
(`*.sql`, `dbt_analytics/*`), cto-reviewer (`scripts/*`, `tests/*`, `frontend/*`),
data-engineer-reviewer (`supabase/*`), equity-analyst-reviewer (`docs/data_contract.md`).
Eleven rounds. Each section summarises rather than enumerating; only the final verdict is a
bare line. Every reviewer was re-run against this exact hash rather than carrying a standing
verdict forward from an earlier artifact.

## What shipped

`supabase/migrations/018_atomic_card_export.sql` defines `replace_cards_snapshot(payload jsonb)`:
one transaction that deletes every `(market_code, snapshot_date)` pair the payload carries and
re-inserts, returning the row count. Guards run before any mutation: payload must be a non-empty
JSON array, every element must carry a non-empty `market_code` and `snapshot_date`, and a key
naming no insertable column raises rather than being silently dropped by
`jsonb_populate_recordset`. The insert lists only payload-carried columns, so a column the
export does not send keeps its DEFAULT, and generated columns are excluded by
`attidentity`/`attgenerated` rather than by the name `id`.

`scripts/export_to_supabase.py` calls it once instead of upserting in batches of 500, verifies
the returned count against what it sent, and adds `order by market_code, ticker, snapshot_date`
so the payload is deterministic. Two failure paths, both exit non-zero: a count mismatch, and an
unreadable response, which deliberately refuses to claim a rollback it cannot know happened.

`frontend/explore_filters.py`'s `attach_assessments` withholds the health verdict and AI read
when the assessment's `snapshot_date` differs from the card's, so the delete cannot leave a card
showing a verdict computed from numbers it is not displaying.

## Verification

`pytest tests/ -q` 615 passed. `sqlfluff lint dbt_analytics/models dbt_analytics/tests` clean
(exit 0, verified by cto-reviewer and analytics-engineer-reviewer independently, the latter
after correcting a false EXIT=1 caused by reading `$?` through a pipe).
`check_dbt_sql_structure.py` passes. Zero em-dashes in 1,050 added lines.
`.claude/active_work.md` staged at 31,961 bytes, under the 32,000-byte cap.

Function semantics verified against the `dev` schema over psycopg2, since dev is not exposed to
REST: a multi-date payload accepted and both dates replaced (1,000 rows, 2.07s); a column
omitted from the payload keeps its DEFAULT; an unknown column raises; the empty and
missing-field guards fire; a failure injected on the last row leaves the table byte-identical
with no canary row leaked; and re-exporting one market left the other five byte-identical.

Mutation-tested rather than asserted. cto-reviewer ran 22 mutants across two rounds and killed
every reachable one: gate deleted, gate reduced to a bare `str()` compare, gate made
one-directional in each direction, `_snapshot_sort_key` truncated to month and to year
precision, the count check neutered, the unverified branch returning 0, the `order by` dropped
and reduced to a non-total prefix, `inserted_count` accepting a bool or a wrong-length list, the
rpc renamed, and a restored batch-upsert loop. Three survivors were analysed and none is a
defect: an over-count is unreachable from `get diagnostics`, and two are pre-existing lines
outside this diff.

## scope-auditor

Failed in rounds 5, 6, 7, 9 and 10; passed here. Its findings drove most of this cycle: an
undocumented gate, a handover contradicting its own contract, a round count wrong in one staged
file while another said otherwise, an eviction claim falsified by two other files in the same
diff, and a stale sentence stating a failure mode this branch had itself changed, two lines
below a line the diff rewrote. In the final round it re-derived every numeric claim by counting
rather than trusting the prose, and confirmed all 19 staged paths are inside `scope_paths`.

It judged the `.gitignore` addition scope creep in its own words, "a scope decision that was
made, not asked", and the amendment records it that way, keeps the line, and claims no approval.

VERDICT: PASS

## cto-reviewer

Failed in rounds 5, 6 and 8. It found the card-contradiction that produced the frontend gate,
the stale-prose sites the author's sweeps missed, a surviving month-precision mutant caused by
test dates a month apart when the real mismatch is one snapshot, and, in round 9, that the
staged-diff hash used to label the first nine rounds was the wrong kind entirely:
`commit_review_gate.py` matches a 64-char sha256 of `git diff --staged --no-renames
--no-abbrev`, not the 40-char `git hash-object` value being recorded. Nine rounds had been
performed for a gate that would have rejected every one of them.

Asked to rule on whether further rounds were paying, it first said no, then corrected itself:
it had keyed the stopping rule on the file type of remaining findings rather than their kind,
and round 10's two prose findings were substantive. It then made the condition checkable
instead of estimated, on the grounds that a rename leaves a finite enumerable set of stale
sites, and verified by grep that both renamed concepts are fully swept.

Its stopping rule, adopted here: a further round is justified only by a factual contradiction,
two sites asserting incompatible things or a claim contradicted by code inside its own file.
Rewording, tone, emphasis and scope opinions on inherited text are follow-ups, not rounds. It
applied that rule against a colleague's outstanding nit and classified it a follow-up.

VERDICT: PASS

## data-engineer-reviewer

Established that the migration's DEFAULT-preservation comment overclaimed, since `payload_keys`
unions across elements, and bounded the severity by showing the only two DEFAULT columns are
also NOT NULL, so a divergent row aborts rather than landing wrong values. Found the false
"eleven `numeric(10,4)` caps" figure the handover inherited from the earlier audit and
republished. Confirmed leaving `014_fr_cac40_market.sql` unedited was correct, citing a recorded
precedent that applied migrations are immutable, and verifying that the runner tracks by
filename with no checksum: "editing it would have been the finding, not leaving it."

In the final round it traced all five legs of the corrected rolled-back-ticker claim to source,
and verified the premise the analysis rests on, that nothing has ever deleted from this table,
by grepping every migration.

VERDICT: PASS

## analytics-engineer-reviewer

Confirmed the mart grain survives the delete-then-insert, with the unique constraint as an
in-transaction backstop, and that the frontend gate is a filter rather than misplaced
computation. Caught that four existing `attach_assessments` tests had become vacuous, comparing
`str(None)` to `str(None)`, so deleting the gate outright left them green. Blocked in round 10
on the last site in the repo asserting the operating metrics are unsourceable for financials,
twenty lines below the code disproving it.

In the final round it traced the corrected claim across staging, base and core rather than
locally, finding zero sector predicates upstream, and re-ran both dbt gates after correcting a
false failure from reading `$?` through a pipe.

VERDICT: PASS

## equity-analyst-reviewer

Endorsed withholding the verdict rather than showing a mismatched one: silence is not false, a
verdict computed from numbers the reader cannot see is. Found that the suppression is permanent
for one case, not transient as the docstring claimed. Found the branch had reintroduced a
bank-specific framing that an earlier finding of its own had already corrected, in the handover,
in the question put to the owner, and in the title of the filed issue. Found the eligibility
note asserting a data-sourcing fact as the reason for a rule that keys on sector alone, which
was false for much of the sector it affects.

In the final round it judged the replacement reason on financial substance rather than wording,
and confirmed no user-facing card copy changed anywhere in the diff.

VERDICT: PASS

## Owner decisions

Three were put to the owner and answered; all are recorded in `contract.md` with the rejected
alternative and its cost, and with the arguments labelled as the author's rather than the
owner's.

- `grant delete on public.mart_stock_cards to service_role`: granted.
- The delete can roll a ticker back to an earlier snapshot, or drop it from the deck when the
  covered pairs take all its rows: accepted.
- A `financial` company-type card whose health block is withheld loses
  `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`: left as is, filed as issue #11.

One remains OPEN and cannot be closed by reviewing: there is no automated coverage of the SQL
function, since every test uses a fake client. Closing it needs a `services: [postgres]`
container in CI, which is a new CI mechanism and so the owner's call. The tally that matters for
that decision: three consecutive rounds found real defects in this untested surface, two of them
in the SQL itself.

## Follow-ups, disclosed not fixed

- `frontend/explore_filters.py` uses "evicted from its newest snapshot" for the rollback case,
  where `docs/data_contract.md` now reserves "evicted" for the all-rows-deleted case. True as
  written; a terminology collision in an internal docstring.
- The corrected `int_stock__card_metrics.sql` comment explains why the leverage and
  cash-conversion metrics are dropped for financials but not why `ebit_margin_pct` and
  `revenue_growth_yoy_pct` are. Incomplete, not false; `docs/data_contract.md` is complete.
- `.claude/active_work.md` has an ambiguous pronoun in "three review rounds found real defects
  in it"; the contract carries the precise version.
- `dbt_analytics/models/_docs.md`'s four docs blocks are orphaned, with no `{{ doc(...) }}`
  reference anywhere in the project. Pre-existing.
- `scripts/assessment_rules.py` uses "Banks:" as shorthand, disambiguated nine lines below, and
  `tests/frontend/test_card_ui.py` says "bank-specific caveat". Both pre-existing and out of
  scope, the latter left on scope-auditor's explicit recommendation.
- `scripts/export_to_supabase.py`'s `if not records: return 0` means an empty mart exits green,
  so the function's empty-payload guard is unreachable from its only caller. Pre-existing,
  fail-safe in outcome, and changing the exit code alters the CI success contract.
- `dbt_analytics/seeds/metric_catalogue.csv`'s applicability strings say "banks" for rules that
  cover the whole `financial` type, and now disagree with `docs/data_contract.md` about the
  reason. User-facing copy, so the owner's call: filed as issue #12.
- `.claude/active_work.md` is structurally at its cap with 39 bytes spare. It needs a rolling
  archive, not another trim.
