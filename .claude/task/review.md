# Review

diff_sha256: ab0546d13e9f07e16c21cfdecb31b57420b5724eceaf0d5138eb9614a8e1adf1

Three rounds. Real findings each round, all fixed or escalated to the owner and decided
before the next round — see `.claude/task/contract.md`'s `amendments` for the full account.

- Round 1 (scope-auditor): FAIL — `st.link_button` (the card footer's "Yahoo Finance" link)
  was missed by the original button inventory (only `st.button(` was grepped) and stayed
  unstyled; a stale comment in `styles.py` contradicted a newer one about the same mechanism;
  the claim that the segmented control is unaffected by the widened selectors was asserted,
  not proven the way the row-overlay-button claim was. Fixed: added a link-button rule (which
  surfaced a second, deeper bug — the real testid is `stBaseLinkButton-secondary`, not
  `stLinkButton`, so a pre-existing footer-scoped sizing rule had silently matched nothing
  since before this slice started); fixed both; corrected the stale comment; verified the
  segmented control's `kind` values live (`segmented_control`/`segmented_controlActive`,
  distinct from `primary`/`secondary`).
- Round 1 (cto-reviewer): PASS — independently verified `stExpander`/`stPopoverButton` against
  the pinned `streamlit==1.57.0` static bundle, the row-overlay specificity math, and the full
  button/popover inventory.
- Round 2 (scope-auditor): FAIL — a duplicate top-level `amendments:` key left in the contract
  from a sloppy edit; `review.md` still showed a different, unrelated prior task (expected —
  written last, not yet reached); the pre-existing footer-rule bug fix was bundled in without
  recorded owner authority. Fixed the duplicate key; escalated the bundling question.
- Round 2 (cto-reviewer): ESCALATE — same bundling question, plus whether the new link-button
  skin should cover the unused `-primary`/`-tertiary` variants. Both put to the owner directly
  and decided: keep the bug fix bundled (same file, same root cause); cover all three variants
  now so a future one never silently ships unstyled.
- Round 3 (scope-auditor): PASS — re-verified the duplicate-key fix, both owner decisions
  against the actual CSS (not just the narrative), and the full widget inventory.
- Round 3 (cto-reviewer): PASS — re-verified the `-primary`/`-tertiary` CSS values property-by-
  property against `button[kind="primary"/"secondary"]`, the testid strings against the actual
  installed Streamlit bundle, and noted (not a defect) that pytest's 145-pass result carries no
  regression signal for this specific diff since nothing imports `styles.py` — the real
  verification is the DOM/selector checks and the screenshots sent to the owner in-session.

## scope-auditor
VERDICT: PASS
risks_checked:
- Duplicate-key regression re-checked directly (grepped for `^amendments:` etc.) — one hit
  each, the round-2 stray leftover is gone.
- Both owner-decision amendments checked against the actual CSS, not just the prose — the
  `-primary`/`-secondary`/`-tertiary` rules in `frontend/styles.py` match exactly what was
  decided.
- Full button/link_button inventory re-run independently via grep — matches the contract's
  claimed inventory exactly, no omitted or extra call site.
- Footer-scoped rule checked for silent override of the new global link-button skin — it only
  sets font-size/min-height/padding/text-decoration, no color/border/radius, so no conflict.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `-primary`/`-tertiary` CSS values diffed property-by-property against
  `button[kind="primary"/"secondary"]` — exact match plus the necessary added `border-radius`
  (`<a>` elements aren't reached by the `<button>`-scoped radius rule).
- `stBaseLinkButton-{kind}` and `stPopoverButton` testid strings verified against the actual
  installed `streamlit==1.57.0` compiled JS bundle, not memory or the contract's narrative.
- Segmented-control non-leak re-derived independently from the same bundle (`kind` values
  `segmented_control`/`segmented_controlActive`, distinct from `primary`/`secondary`).
- Row-overlay tap-button invisibility re-derived via CSS specificity math — (0,4,2) beats
  (0,1,1) regardless of source order even with `!important` on both sides.
- Full widget-call inventory (buttons/popovers/expanders/link_button) re-verified by grep —
  exact match, no missed consumer.
