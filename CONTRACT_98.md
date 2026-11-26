# CONTRACT_98: pre-registered scorecard for Synthetix UI

Status: **FROZEN** at the commit that introduces this file (step 10 of docs/PLAN_98.md), before any new measurement
(the new measurements are the Pinterest-screenshot captures taken in session 1, committed after this file).

Rules that go with this rubric (also in CLAUDE.md and .github/copilot-instructions.md):

1. No threshold, weight, point value or definition in the table below may change after measurements exist.
   A threshold that looks wrong is proposed in `reports/AMENDMENTS.md` and waits for Daniel. Nothing is waived.
2. A score is a number produced by a script from files in the repo. A component without evidence is `NOT MEASURED`
   (not zero, not an estimate). A total /100 and a likeness /10 are printed only when every fidelity component has evidence;
   otherwise the report says `partial, X evidenced of 100`.
3. The scorer is frozen: `tools/scorer/*` and every file listed in `reports/scorer.lock.json` (CI verifies the hashes, step 8).
4. Held-out strings (`reference/split.json`) are never used for fitting, tuning or choosing between candidates.
5. Originality: no Pinterest font file is downloaded, extracted, decompiled or used; no reference screenshot is auto-traced.
   Outlines come from `tools/glyph_dna.py` parameters fitted to measurements. Instrument Sans stays the OFL base; OFL.txt stays intact.
6. Definition of done: total >= 98 and likeness >= 9.9, produced by scripts in CI on a clean clone with matching SHA-256s,
   zero open critical defects, nothing waived, every amendment listed in `reports/AMENDMENTS.md` and approved by Daniel.

## Rubric: how 98/100 and 9.9/10 are defined

The contract refuses to print a 0-100 number. This rubric is committed as CONTRACT_98.md before any new measurement (same rule as V4: thresholds never move after seeing results). Full marks need the 98-tier threshold, which is stricter than the contract's.

| Component | Pts | Full marks when |
| --- | --- | --- |
| Shape IoU vs reference | 20 | median >= 0.93 and every Match glyph >= 0.88 |
| Glyph widths | 8 | within 0.5 px on >= 98% (letters, digits, punctuation) |
| Held-out pair gaps | 10 | within 1 px on >= 95% of held-out pairs |
| Vertical metrics | 5 | all within 1 px, every weight |
| Stems | 7 | within 3% in 400/600/700 from real references |
| String render match | 5 | blur-normalised SSIM >= 0.95 on held-out UI strings, 3 sizes |
| Font Bakery | 8 | 0 FAIL on every shipped file |
| Coverage | 4 | all 324 Latin Core + official African list |
| Confusables | 5 | all 7 pairs <= 0.65 |
| Kerning review | 5 | named pairs approved by 2 reviewers |
| Engines and OS | 7 | Chromium, Firefox, WebKit, Android, iOS/CoreText, Windows agree |
| Real screens | 6 | one per platform |
| Name clearance | 4 | decision made, registries searched |
| Legal/originality review | 3 | consult recorded |
| Distinct from Instrument Sans | 3 | blind review passes |

Fidelity = 55 pts, Quality = 35, Identity/legal = 10. **Likeness /10 = 10 x fidelity pts / 55**, so 9.9 needs >= 54.5 of 55. **98/100 allows 2 points of slack in total.**

Two amendments, recorded openly (not waivers): (a) the blind review compares Synthetix to Instrument Sans only, because "identical to the target" and "reviewers can tell it from the target" cannot both be goals; (b) confusables are scored in ID mode (ss13 + zero) as V4 decision 5 proposes, since the reference's own I and l are near-identical (0.133 vs 0.126 cap).

Originality line: likeness comes from measured proportions and outlines drawn from measured specs. Never trace or extract the reference font. This matches your IDENTITY_DIRECTION.md; step 102 is the legal check.
