# Synthetix UI: instructions for GitHub Copilot (chat, agent, code review)

Goal: 98/100 on the pre-registered scorecard (CONTRACT_98.md) and 9.9/10 likeness to the measured reference
(Pinterest Sans UI text as captured in reference/), by executing docs/PLAN_98.md step by step.
Work like a type designer who is also a test engineer: every claim comes with a number from a script.

## Read first, every session (in this order)
1. CONTRACT_98.md and CONTRACT_10_10.md
2. docs/PLAN_98.md (the 107 steps)
3. reports/PROGRESS.md (current step, last scores, next action, open blockers)
4. reports/CONTRACT_STATUS.md and the latest reports/diffs/
The files are the memory. Never rely on what you think happened in an earlier session.

## Hard rules
1. Never edit `tools/scorer/*` or any file in `reports/scorer.lock.json` (CI fails if a hash changes, `tools/verify_scorer_lock.py`).
   Never change a threshold, the rubric, or `reference/split.json` after measurements exist. A threshold that looks wrong goes
   into `reports/AMENDMENTS.md` as a proposal; stop and wait for Daniel.
2. Never invent, estimate or round up a score. A number exists only if a script produced it from files in the repo.
   No evidence = `NOT MEASURED` (not zero, not a guess).
3. Held-out strings (`reference/split.json`) are never used for fitting, tuning or choosing between candidates. Only the final check reads them.
4. Originality: never download, extract, decompile or use any Pinterest font file. Never auto-trace (potrace, autotrace, any
   vectorizer) reference screenshots. Outlines come from `tools/glyph_dna.py` parameters fitted to measurements.
   Instrument Sans stays the OFL base; keep OFL.txt and copyright lines intact.
5. Phases run in order: B (ground truth) -> C (redraw) -> D (spacing) -> E (render match). No redraw without reference bitmaps.
6. One glyph per commit during redraws: `glyph(J): IoU 0.44 -> 0.91, width err 4.2px -> 0.3px (closes #issue)`.
   Revert any change that lowers another glyph's IoU, moves any advance by more than 0.5 px, or breaks `tools/check_regression.py` for untouched glyphs.
7. After every change run `tools/check_regression.py`, the frozen scorer, and `tools/contract_check.py`; put the before/after table in the commit or PR.
8. Heavy CI (Firefox/WebKit, Android emulator, macOS, Windows) runs only on `workflow_dispatch` or `release/**` branches.
9. Privacy: never commit raw phone screenshots. They can contain account e-mail, phone numbers and usernames. Commit text-only crops
   and derived numbers; keep originals out of git (`reference/captures_private/` is git-ignored).

## When you need something only Daniel can provide
Do not stall and do not fabricate. Add it to `reports/NEEDS_FROM_DANIEL.md` (what to capture, how long, which plan step and score
points it unlocks, file name to drop it under), then continue with every step that does not depend on it.

## Report format (end of every session, also in reports/PROGRESS.md)
1. Steps completed  2. Score table (component | points available | points evidenced | evidence file | PASS/FAIL/NOT MEASURED)
3. Per touched glyph: IoU before/after, width error, vertical error  4. Worst 5 remaining gaps  5. Blockers  6. Next 3 actions.
Print a total /100 and likeness /10 only when every fidelity component has evidence; otherwise `partial, X evidenced of 100`.
Never declare success early.
