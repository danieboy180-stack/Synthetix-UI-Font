# Amendments to CONTRACT_98

Rule: a threshold or definition changes only through this file, and only with Daniel's written approval.
Nothing here is a waiver. Status column is `PENDING` until Daniel signs off in this file.

| # | Amendment | Source | Effect on rubric | Status |
|---|-----------|--------|------------------|--------|
| A | "Distinct from Instrument Sans" blind review compares Synthetix to **Instrument Sans only**, not to the reference. "Identical to the target" and "reviewers can tell it from the target" cannot both be goals. | docs/PLAN_98.md section 2(a) | Defines what the 3-point Identity component measures; no threshold moved. | PENDING Daniel approval |
| B | Confusables are scored in **ID mode (ss13 + zero)** per V4 decision 5, because the reference's own I and l are near-identical (0.133 vs 0.126 cap). | docs/PLAN_98.md section 2(b) | Defines the mode in which the 7 pairs are scored; threshold (<= 0.65) unchanged. | PENDING Daniel approval |

Proposals raised during execution (none yet) are appended below with the measured evidence that motivates them.

## Proposals raised in session 1 (PROPOSALS ONLY: nothing changed, the frozen scorer and every threshold are untouched)

| # | Proposal | Evidence | What it would change | Status |
|---|----------|----------|----------------------|--------|
| C | Make the **stem measurement method identical for reference and font** (area/coverage sum on both) before the Stems component is scored. The frozen scorer measures the target and the candidate by different procedures. | Same-method re-measure (reports/session1/SCREENSHOT_MEASUREMENTS.md): only 5 of 10 stems are within 5% and 3 of 10 within 3%; vertical stems are 11-18% too heavy while the frozen scorer reports 9/11 within 5%. Reference V/H stem ratio 0.997 vs Synthetix 1.135. | Method only, no threshold. Cannot be resolved by code: needs a Synthetix render on the same device (plan Phase E) to separate renderer effects from design. | PENDING Daniel approval |
| D | Register the **IoU alignment method** before the Shape IoU component is scored: baseline row + ink-left edge, 50% threshold, cap normalised to 128 px (tools/glyph_iou.py). Sidebearings are scored by the width gate, not by IoU. | The frozen scorer has no IoU code. Best-horizontal-shift gives a secondary bound (letters median 0.853 vs 0.828). | Defines the method; thresholds (median >= 0.93, every Match glyph >= 0.88) unchanged. | PENDING Daniel approval |
