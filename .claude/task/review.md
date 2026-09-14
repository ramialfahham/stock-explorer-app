# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 9b947e3ec4dd7b594eb59dac693a29044dca046181fea23dcbed8349fcd36f8a

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `scripts/*`,
`tests/*`, `requirements*.txt`). Three rounds.

## What shipped

The black screen on load. Header before the storage read and the deck fetch, with a
"Loading cards" line; a splash written into Streamlit's index.html at deploy time so the
first byte shows the product; the saved list moved from the streamlit_extras localStorage
component to cookies Streamlit reads on the first run, written by a components.html script
only in a run that saved or cleared, with a one-time verified migration of a legacy
localStorage list. streamlit-extras removed; Streamlit telemetry off. Verified live on the
local server: a save writes `ss_saved_0`, a fresh session reads "1 saved", no iframe on a
plain load. 706 tests.

## Round 1

cto: a crafted cookie (12-digit or 5000-digit epoch) raised out of the first run and left
that browser on a traceback for the cookie's lifetime; the migration removed localStorage
before checking the cookie landed and wrote one unchunked cookie (over about 140 saves,
silent loss); nothing tested that `flush_storage_writes()` fires after a save. All three
fixed and mutation-proven. scope-auditor: `docs/supabase_setup.md` still said localStorage;
the Render build step is a new mechanism and is now recorded as one with its provenance.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Cookies over a lighter component (A, chat). Open for the owner: the two new strings
("Loading cards"; splash "Stock Explorer" / "Loading"), the migration (unrequested, kept so
no saved list vanishes), the build step itself (proposed as step 2 before "Now solve it").
