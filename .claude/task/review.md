# Review

diff_sha256: 8551e3829f20c1c5ea3170785758c6e135cd3f70e3e9759d12946be04ccca5f7

One review round. Required reviewers per routing (`.claude/review_routing.json`): scope-auditor
(always), cto-reviewer (`frontend/*`, `tests/*`). No dbt or `docs/data_contract.md` file in this
diff, so analytics-engineer-reviewer and equity-analyst-reviewer are not required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before dispatch and never moved while reviewers were running.

**Final verdicts (round 1, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Fixes the Discover list's verdict-dot alignment. The owner reported the health-verdict dots
looked "scattered" down the list. Live measurement in the running app confirmed every row's own
flexbox layout was already pixel-identical (bounding-box offset exactly 0.0 across every
sampled row); the misalignment was the native color emoji's (🟢/🟡/🔴) own internal vertical
glyph metrics, which vary by platform/font and are outside CSS's control. Replaces the emoji
character with a plain CSS-drawn circle, same three colors, same meaning, pixel-exact by
construction. Explicitly does not add a visible text label next to the dot: the owner correctly
flagged that a word (e.g. "Healthy") sitting beside the row's one displayed metric would read as
if it rated that specific number, when the verdict is actually derived from 3-6 different
metrics depending on company type. The label only reaches the dot's `aria-label` (using the
already-existing, already owner-approved vocabulary `VERDICT_BADGE_LABEL`), never visible text.
The full card's own separate verdict badge (`card_ui.py`) is untouched, since it renders once
per card, not repeated hundreds of times down a scrolling list, and doesn't exhibit the
alignment problem this task fixes.

## Round-by-round findings and fixes

**Round 1**: both required reviewers passed clean on the first pass. Both independently traced
the one edge case worth checking closely, a potential `KeyError` in
`VERDICT_BADGE_LABEL[token]` when a card has no assessment yet, and confirmed
`health_verdict_token` only ever returns `None` or a key already present in both
`VERDICT_EMOJI` and `VERDICT_BADGE_LABEL`, so the ternary's short-circuit means the falsy-token
path never touches the dict. Both also independently verified, directly against the diff rather
than the contract's own claim, that no visible text label was added anywhere (the label reaches
only the `aria-label` attribute), and that `frontend/card_ui.py`'s separate, untouched verdict
badge still works unchanged. scope-auditor additionally ran the full `tests/frontend` suite live
(166 passed) rather than trusting the reported count.

## scope-auditor
VERDICT: PASS
risks_checked:
- No stale caller of `build_rich_row_html`/`render_rich_row_list` still passing the old
  `str | None` verdict shape: repo-wide grep confirms `frontend/app.py` is the only caller;
  Saved/Search use the untouched `build_row_html`/`render_row_list` path, which takes no
  verdict argument at all.
- The "no visible text label" claim holds in the actual live code path, not just the new test:
  traced `_discover_row_verdict` through its single call site into `build_rich_row_html`'s only
  verdict-rendering branch, confirming the label reaches only `aria-label`, never element text.
- `frontend/card_ui.py` (the full card's own verdict badge) is untouched: not part of the diff,
  live-read confirms it still imports and renders `VERDICT_EMOJI`/`VERDICT_BADGE_LABEL`
  unchanged.
- New and updated tests are genuine, non-tautological regression tests, confirmed by running
  the full `tests/frontend` suite live (166 passed), not asserted from the contract.
- Doc-sync: `docs/ui/discover_list.md`'s wireframe and prose updated accurately;
  `docs/ui/design_system.md` checked for drift and found no stale claim.
- No em/en dash on any added line, scanned programmatically across the full patch.
- Both hash checks passed: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch are identical.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `KeyError` risk in `_discover_row_verdict`'s `VERDICT_BADGE_LABEL[token]` lookup when a card
  has no assessment: traced `health_verdict_token` and confirmed it only ever returns `None` or
  a key already present in both `VERDICT_EMOJI` and `VERDICT_BADGE_LABEL`; the ternary's
  short-circuit means the falsy-token path never touches the dict.
- Incomplete refactor or dead references: grepped the full repo for `verdict_emoji` and the raw
  emoji glyphs; found none left in `row_ui.py`, `app.py`, or the updated test file, and
  confirmed the pre-existing emoji usage in `card_ui.py`/`test_card_ui.py` is the deliberately
  out-of-scope full-card badge, untouched.
- The escaping test exercises both the verdict label and the metric independently, not just one
  side.
- The three new `--ss-verdict-*` tokens sit inside the `:root` block, not orphaned; the old
  emoji-sizing CSS rule is fully replaced, no dead CSS left behind.
- No em/en dash on any added line.
- Both hash checks passed.
