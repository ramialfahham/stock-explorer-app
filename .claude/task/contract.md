# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner request: replace the single README screenshot with 4 new ones the owner
  supplied directly into `docs/media/` (Discover list, search, and the two halves of an
  opened card's detail view), plus a recorded demo GIF of the same interaction, laid out
  GIF-on-top with the 4 stills below (owner-confirmed layout). Recorded via Claude in
  Chrome's `gif_creator` against the live Render deploy (search "nvidia" -> open its card
  -> scroll its sector-compared metrics -> back to list); re-recorded once at the owner's
  request without the tool's default click-indicator/action-label/progress-bar overlays,
  which read as busy/debug-looking rather than clean product marketing. Update
  `README.md`'s image block from one `<img>` to the GIF plus a 4-image row with
  descriptive alt text, and remove the superseded `docs/media/discover-card.png`. Also
  fixed a pre-existing, unrelated copy defect the owner flagged separately: "The recording
  below shows the interaction" was calling a static image a recording before this task;
  now genuinely accurate since a real recording exists.

  Not a Streamlit UI change (README/docs asset only), so `docs/working_agreement.md`'s UX
  PR gate (Streamlit layout/copy/interaction) does not apply.

scope_paths:
  - README.md
  - docs/media/discover-card-1.PNG
  - docs/media/discover-card-2.png
  - docs/media/discover-card-3.PNG
  - docs/media/discover-card-4.PNG
  - docs/media/discover-card.png
  - docs/media/discover-demo.gif
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none -- the owner supplied the exact images and directed the
  replacement; alt-text wording for a screenshot gallery is not a product/UX content
  decision on the level `.claude/working-agreement.md` §6 reserves (naming, metric
  definitions, permanent identifiers).

done_when:
  - README.md shows the demo GIF on top and all 4 new screenshots below, with accurate
    alt text, superseded screenshot removed from git and disk.
  - Copy in that paragraph accurately calls it a "recording" now that one genuinely
    exists.
  - Review cycle run (`scope-auditor` per `.claude/review_routing.json`'s `always` rule --
    no other path pattern matches README.md/docs/media), `review.md` written, committed on
    a new branch, MR opened. Not merged -- owner's action.
