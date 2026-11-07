# Synthetix UI V4 - 10/10 Contract

Status: **DRAFT until the owner merges it.** The merge is the owner's commit of record. After the merge, thresholds, the scorer and the reference data change only by a further owner commit, never by an agent run.

Source: `Synthetix_UI_V4_Master_Plan_to_10_10.docx`, sections 3, 6 and 7, transcribed without changing any threshold. Gaps in that text are listed in section 7 and are not filled in.

## 1. Definition

10/10 means all of:

- every hard gate in section 2 passes;
- the Fidelity and Quality scorecards (sections 3 and 4) are each >= 95/100, reported separately and never blended;
- the identity review (section 5) is signed off;
- zero open critical defects;
- nothing waived.

It is a claim about what was tested. What a screenshot cannot prove (true sidebearings, real kerning tables) is left out of scoring, not estimated.

The scorer is frozen and hash-pinned. Any scorer change re-scores V3 as well, so V3 to V4 deltas stay comparable.

## 2. Hard gates (any failure blocks release)

| ID | Gate |
|---|---|
| H1 | Font Bakery universal and Google Fonts profiles: 0 FAIL on every shipped file |
| H2 | Latin Core and Pri-African coverage, plus language-shaping checks for each in-scope language |
| H3 | Tabular figures equal width; no .notdef for any required character |
| H4 | A clean-clone build reproduces the recorded SHA-256 hashes |
| H5 | Variable and static fonts agree within 1 unit |
| H6 | Advance widths identical across Chromium, Firefox, WebKit and the native test apps |
| H7 | OFL text and copyright intact; name clearance recorded |
| H8 | Zero open critical defects |

## 3. Fidelity scorecard (>= 95, thresholds pre-registered)

| ID | Criterion |
|---|---|
| F1 | Shape similarity (IoU) >= 0.85 on 90% of Match glyphs |
| F2 | Letter widths within 1 px for 90% of glyphs |
| F3 | Held-out pair gaps within 1 px for 90% of pairs |
| F4 | Vertical metrics all within 1 px |
| F5 | Stems within 5% in all four weights, measured from real references |

Fidelity is scored only on glyphs the Glyph Decision Register marks Match. Fit on half the glyphs and strings, judge only on the other half.

## 4. Quality scorecard (>= 95)

Components: Font Bakery pass rate; coverage; small-size legibility and confusables; human review of the named kerning pairs; cross-engine rendering; token adoption on real screens. Numeric thresholds are not set (open item O-2).

## 5. Identity review (pass or fail)

Two reviewers use `IDENTITY_DIRECTION.md`. In a blind comparison of Synthetix, Instrument Sans and the reference, they can tell the three apart and say why.

## 6. Rules for agent runs

- One iteration per run. Give it only that stage's section, inputs and exit gate.
- It may not edit the scorer, the thresholds or the reference data.
- Every claim comes with an artifact (report JSON, overlay image or log) saved in `reports/`.
- It reports regressions first and improvements second.
- If a measurement cannot be made (missing reference, missing engine), it says so and stops. It does not substitute an estimate.
- The owner approves glyph shapes by eye at real sizes before an iteration closes.

## 7. Open items (owner closes these before the first V4 build)

| ID | Gap in the plan text |
|---|---|
| O-1 | No weights or formula roll F1-F5 into a 0-100 score. V3's own blended rubric (weights 25 / 15 / 10 / 15 / 15 / 10 / 5 / 5) is one candidate, but the plan forbids blending. Until set, the operative test is that every criterion meets its threshold, and no /100 number is reported. |
| O-2 | The Quality scorecard has no numeric thresholds. |
| O-3 | Name: "Synthetix" collides with an active DeFi protocol (SNX). Keep or rename is undecided; the trademark and domain search record is outstanding. |
| O-4 | "Critical defect" has no severity definition and there is no defect register. |
| O-5 | The frozen scorer does not exist yet. V3's scoring scripts (`tools/evalref.py`, `tools/geometry.py`, `tools/v3/eval_final.py`, `tools/v3/make_scores.py`, `tools/v3/final_checks.py`) are pinned by `baseline/v3/MANIFEST.sha256` but cannot be re-run: the reference screenshots and bitmaps are not in the V3 zip, and 16 of its 18 scripts hardcode absolute paths. V3's 72.1/100 is recorded, not re-verified. |
| O-6 | Reference definition: screenshots with device, OS and app version (Stage 3). Whether the target UI really uses Pinterest Sans is unconfirmed (README, Known limits), so F1-F5 measure similarity to a captured reference, not to "Pinterest Sans". |
| O-7 | The Glyph Decision Register (Match / Keep / Diverge per glyph) is not started. |
| O-8 | "Required character" is undefined, so H2 and H3 (no .notdef for any required character) cannot be fully evaluated. The baseline audit used its own lists (`reports/V3-baseline-audit.md`). |
