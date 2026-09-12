# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 59381553c7812d74e65776f34cc5464cfd07d0c85da09fd5b7b6b5c918c29402

Two reviewers, by routing: scope-auditor (`always`), cto-reviewer (`frontend/*`, `tests/*`).
Two rounds.

## What shipped

On Discover and Saved, while a card is open, the header is the brand alone and the back
button shares one row with the saved count. The AI-written read folds to its first 28 words
behind the card's existing Read more toggle; the verdict badge, block label and financial
caveat stay outside it. Measured at 375x812 on 3M: first metric value 742px (was 978); at
480x812 on 3i: 757px (was 876). 672 tests, including two AppTest cases that drive the real
script through open card, Back and a tab switch.

## Round 1

cto: the Saved card view's back row showed the deck-filtered count while the list showed the
interaction count, so a saved company that had dropped out of the deck made the number change
on tap; fixed to one count. Nothing pinned the header actually compacting at the call site;
two AppTest tests now do, and the inverted-header mutant fails them. scope-auditor: the north
star still called the AI read "always visible"; a sentence credited the two caption lines with
the whole fold loss; `_card_open` was untested; the success check overclaimed Search.

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## Owner decisions

Both levers, chosen in chat on the measured breakdown. The preview length is the agent's.
