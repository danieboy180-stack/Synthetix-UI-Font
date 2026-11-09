# Glyph Decision Register (Stage 1) - PROPOSED defaults

Machine-readable: `reports/glyph_decision_register.json` (626 entries). Decisions: **Match** (follow reference), **Keep** (inherit Instrument Sans), **Diverge** (original). Fidelity is scored only on Match glyphs.
These are proposals derived from recorded V3 evidence; **you confirm or override**. Your 14 priority glyphs and the six you identified are not in this repo.

| Group | Count | Proposed |
|---|---|---|
| V4 new glyphs (hooks, open E/O, dot-below composites, symbols, figures, ss13) | 124 | Diverge: no reference exists; constructed, unreviewed |
| Letters with recorded shape IoU 0.85 or more | 31 | Keep |
| Letters with recorded shape IoU below 0.85 | 21 | Match (structural gap); a redraw needs reference bitmaps |
| Everything else inherited | 450 | Keep |

Below 0.85 (recorded V3 raw IoU; U and s display as 0.85 after rounding but are just under): J 0.44, K 0.63, Q 0.71, i 0.71, R 0.74, a 0.75, y 0.75, Y 0.76, G 0.77, g 0.77, C 0.78, r 0.80, c 0.80, j 0.81, S 0.82, X 0.82, w 0.82, e 0.83, k 0.83, U 0.85, s 0.85.

## Alternates (Step 0, measurable half only; `reports/alternates_audit.json`)
Ink width and tail depth at cap = 49 px against the recorded reference: Q.ss09 tail 8.8 px vs 5 (overshoots by 3.8) and 3.8 px too narrow; K.ss04 3.9 px too wide; a.ss02 1.5 px wide;
J.ss08 is closer than default on width (+2.4 vs -4.2 px) but outside 1 px; R.ss05, G.ss07 and y.ss03 are about equal to default. **No alternate is promoted**: shape similarity cannot be scored without the reference bitmaps, and the plan forbids substituting an estimate.
