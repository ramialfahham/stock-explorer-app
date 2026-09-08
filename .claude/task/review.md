# Review

diff_sha256: 62497e17c1daa00559758b199ab76a686c799762da3e7b244b50e2ab0ff86ec1

Documentation-only change. Routing requires scope-auditor alone: no staged path matches a
`paths` rule (`docs/operations_guide.md` is not one of the two docs routed to
equity-analyst-reviewer), and `always` is scope-auditor. Three rounds; earlier rounds as
prose, only the final round carries a bare verdict line.

## scope-auditor

Round 1 returned FAIL on four findings, two of them hard defects.

The worst was a false justification I had written into the ops guide: that the publishable key
"already ships inside the frontend to every visitor". It does not. Streamlit resolves the key
in `frontend/settings.py` and builds the client server-side in `frontend/supabase_client.py`;
nothing emits it to a browser. The claim also contradicted the paragraph six lines above it,
which correctly says the browser receives only a static shell. Putting that key in a monitor
URL genuinely widens where it exists -- the honest basis for doing so is that it is
publishable by design, with the select-only `anon` policy limiting the REST API specifically.
Rewritten accordingly, and the same false claim was repeated to the owner in conversation and
corrected there too.

Second: `.claude/active_work.md` still instructed a future session to follow the exact GitLab
"Pipeline emails" integration route this change was deleting from the ops guide, and pointed
at that doc for it. A SessionStart-injected handover contradicting the doc it cites is worse
than either being wrong alone.

Third: the `404 Integration Not Found` response was over-read. `GET /integrations` lists only
ACTIVATED integrations and the per-integration endpoint 404s for anything never configured, so
the API establishes "never set up", not "not offered". The absence from the Settings list is
the owner's report, and is now attributed as such in both files.

Fourth: open item 6 was closed while the ping interval was still unrecorded and while
asserting database coverage that cannot be observed for ~7 days. The closure now says it rests
on setup being in place rather than observed effect, the app monitor's 5-minute interval is
recorded, the database monitor's interval is explicitly marked as not captured, and the ops
guide carries a concrete verification procedure.

Round 2 passed with three non-blocking residuals: the RLS justification was overstated in
isolation (the key also reaches Auth endpoints, where the table policy is not the control);
the handover stated the Settings-list claim flatly where the ops guide hedged it; and a reader
of the ops guide alone would see the missing database interval as an omission rather than a
known gap. All three fixed rather than shipped, since two were the same attribution defect
that failed round 1.

Round 3 confirmed all three closed with no new imprecision, and verified the corrected RLS
wording had not swung from over-claiming to under-claiming.

VERDICT: PASS
risks_checked:
- The replacement security justification for the key in the monitor URL is not a second wrong
  claim: verified against `001_initial_schema.sql` (RLS, `for select ... to anon`),
  `011_grant_roles.sql` (select-only grant to `anon`) and `frontend/supabase_client.py`
  (client built server-side, key never emitted to a browser).
- No key value in the tracked tree: only the bare `sb_publishable_`/`sb_secret_` prefixes as
  placeholders. The monitor URL is documented with `<SUPABASE_URL>` and `<publishable key>`.
- Handover and ops guide agree rather than contradict on all three shared claims: the
  integration route, the Settings-list attribution, and the uncaptured database interval.
- Thresholds cited (~15 min Render sleep, ~7 days Supabase pause) corroborated in-repo, and
  the verification procedure's 1st/15th write cadence matches `.gitlab-ci.yml`.
- No em/en/figure dash on any added line, scanned from a file with explicit UTF-8 decoding.
  `.claude/active_work.md` at 29,795 bytes, under its 32,000-byte injection cap.
- Nothing here is a §6 owner decision: the owner configured both monitors and the notification
  themselves; this change only records what exists.
