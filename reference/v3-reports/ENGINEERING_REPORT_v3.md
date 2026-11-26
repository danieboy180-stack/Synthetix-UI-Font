# Synthetix UI v3: Engineering Report

**Final verified score: 72.1/100 = 7.2/10.** Baseline v2 under the same rubric: 43.1/100 (4.3/10); plain Instrument Sans: 29.2/100. The 9/10 target (90/100) was **not reached**. The missing 18 points are listed in section 11. v2's own preliminary '8/10' was not supported by this rubric.

Two separate outcomes (never to be confused):

- **A. Typographic metric fidelity** (widths, vertical, stroke, spacing): 44.5/55 = **8.1/10**.
- **B. Actual visual identity fidelity** (glyph geometry): 14.9/25 = **6.0/10**. 31 of 52 glyphs reach IoU >= 0.85 (the report's identity threshold); glyph outlines are still Instrument Sans's.

## 0. Evidence basis and confidence handling

- Reference = the screenshot-based **Forensic Report**, not an official font. Confidence classes are preserved: **HIGH** (directly measured: glyph ink boxes, vertical metrics, pair gaps, stems at the primary scale) were used as targets; **MEDIUM** (weight-class interpolations, 214-unit word space) used as targets but labelled; **LOW** (sidebearings, advance widths, Medium/SemiBold horizontal-stroke ratios) used only as hypotheses; **PROPOSED** (UPM 1000, cap 700, x 500, ascender 729, descender 171/186, hhea 950/-250) adopted as a *design grid*, not as fact.
- Independent recalculation of the report: **0 arithmetic discrepancies** across glyph boxes (W = x1-x0+1), advances (W+LSB+RSB), W/cap ratios, all 50 alphabet pair gaps recomputed from boxes, word totals, unit conversions (px x 700/49), and both weight-interpolation formulas. An independent extraction of the same screenshot agreed with the report's 52 letter widths to a mean of 0.33 px (max 1 px).
- **Not independently validatable:** true advance widths/sidebearings, real UPM, real kerning tables, whether the app UI ships Pinterest Sans, weights above 600, the horizontal-stroke ratio of Medium/SemiBold, behaviour in Firefox/Safari (not installed here), WOFF2 output (no brotli here).

## 1. Technical audit of Synthetix UI v2 (baseline)

**Fonts.** The HTML embeds three static WOFF files (zlib), no variable axes, no STAT. Family `Synthetix UI`; subfamilies Regular / SemiBold / Bold; PostScript `SynthetixUI-Regular|SemiBold|Bold`; version `Version 1.000; modified from Instrument Sans 1.000`; UPM 1000; 501 glyphs, 343 code points, 268 composite glyphs; copyright and OFL name records preserved; no TrueType instructions (unhinted). Tables: GDEF GPOS GSUB OS/2 cmap gasp glyf head hhea hmtx loca maxp name post prep. OS/2 weight classes 400 / 600 / 700; hhea 970/-250/0; OS/2 cap 720, x 510; GPOS kerning inherited unchanged (1661 glyph pairs + class cells).

**CSS.** Three @font-face rules (400/600/700) with `size-adjust:108%`; Instrument Sans for comparison rows is loaded from Google Fonts (external). `letter-spacing` appears only on UI chips; `font-kerning:normal`; lining proportional numerals; no `font-synthesis` control; fallback stack `system-ui...`.

**Contradictions between the v2 claims and the actual files:**

- Weight labels are wrong. The three masters were cut at Instrument Sans wght **420 / 500 / 610**, i.e. Regular / **Medium** / **SemiBold**-class, but are labelled and mapped as 400 / **600** / **700**. The report's classes are 400 / 500 / 600; there is no evidence of a Bold.
- A global tracking of +14 / +11 / +7 units was baked into **every glyph advance** (letters, digits, punctuation, ligatures). It widened alphabet pair gaps: RMS error vs the report went from 1.20 px (plain Instrument Sans) to **1.89 px**, and only 55% of pairs stayed within 1 px (plain: 80%). It compensated for narrow glyph ink instead of fixing it.
- Inherited kerning was not re-tuned after width edits and tracking.
- `size-adjust:108%` is a CSS compensation for an unknown cap/em ratio (it assumes cap/em 0.72 and the 4.5 px/css-px scale); it is not a glyph-geometry correction.
- 'Held-out 0.97 css px' was leave-one-text-out over texts that also fitted the tracking, drawn from the same screenshots; it is not independent validation. Under a truly held-out test v3 reaches 0.79 px.
- 'Vertical within 0.6%' was verified on Regular only; Q tail depth (1 px vs 5 px), stroke contrast (E arms 5.0 vs 6.0 px) and horizontal/vertical stroke ratio were never measured.
- '8/10' is unsupported: under the stated rubric v2 scores 4.3/10.
- Inherited coverage gaps: no U+20A6 (Naira), U+20B5, U+20B9, U+2116, U+2713 (check mark, which the Pinterest UI uses), U+2260, U+2264, U+2265, U+00BD.
- No WOFF2 files; comparison rows depend on an external CDN.

## 2. Measurement framework

All measurements use real Chromium (`--font-render-hinting=none --enable-font-subpixel-positioning`, DPR 1, grayscale AA), at cap height = 49 px (the report's primary scale), mirroring the report's method: ink = luminance <= 160, 8-connected components, per-glyph boxes, baseline = median bottom of flat-bottom glyphs, gap g(i,j) = x0(j) - x1(i) - 1, stems from sub-pixel coverage sums. Formulas: relative error = (C-R)/R x 100; MAPE = mean |relative error|; string error = |C-R| and |C-R|/R x 100; pair-gap RMS = sqrt(mean (C-R)^2) in px; shape fidelity = IoU of binarised glyph bitmaps aligned on baseline and ink-box centre (also width-normalised). Pass rules used by the rubric: width |C-R| <= 1 px (the report's own tolerance), vertical |C-R| <= 1 px, stem within 5%, gap within 1 px, IoU >= 0.85.

## 3. Measurement results (Regular vs report, cap = 49 px)

| Metric | Reference | Plain Instrument Sans | v2 | **v3** |
|---|---|---|---|---|
| cap H (px) | 49 | 49 | 49 | 49 |
| x-height flat (v,w,x,z) (px) | 35 | 35.0 | 35.0 | 35.0 |
| ascender l (px) | 51 | 49 | 51 | 51 |
| ascender b,d,h,k (px) | 51.5 | 49.0 | 51.0 | 51.0 |
| desc p,q,y (px) | 12 | 14.0 | 12.0 | 12.0 |
| desc g,j (px) | 13 | 15.0 | 12.0 | 13.0 |
| t height (px) | 45 | 45 | 45 | 45 |
| digit 1,4,7 height (px) | 49 | 49.0 | 49.0 | 49.0 |
| Q below baseline (px) | 5 | 1 | 1 | 1 |
| ink width A-Z (px) | 1207 | 1201 (-0.5%) | 1227 (+1.7%) | 1203 (-0.3%) |
| ink width a-z (px) | 955 | 919 (-3.8%) | 948 (-0.7%) | 951 (-0.4%) |
| ink width pangram (px) | 1209 | 1151 (-4.8%) | 1183 (-2.2%) | 1198 (-0.9%) |
| ink width digits 0-9 (px) | 396 | 378 (-4.5%) | 387 (-2.3%) | 393 (-0.8%) |
| glyph width MAPE, 79 glyphs | - | 7.76% | 5.50% | 4.01% |
| glyphs within 1 px of reference width | 79 | 30 | 52 | 68 |
| pair-gap RMS, alphabets+digits (px) | 0 | 1.20 | 1.89 | 1.09 |
| pair gaps within 1 px | 49 | 39 | 27 | 40 |
| pangram within-word gap RMS (px) | 0 | 0.85 | 1.21 | 0.98 |
| word-space gaps within 1 px | 6 | 4 | 3 | 5 |
| glyph shape IoU (mean, aligned) | 1 | 0.780 | 0.819 | 0.850 |
| glyphs with IoU >= 0.85 | 52 | 15 | 20 | 31 |

**Held-out UI strings** (37 strings: 9 original samples + 28 menu items at 3 display sizes; v3 was never fitted on them, v2 was):

| | Plain | v2 (fitted on them) | **v3 (held out)** |
|---|---|---|---|
| mean glyph x-error (css px) | 1.05 | 0.79 | 0.79 |
| mean absolute string-width error | 1.43% | 0.87% | 0.94% |
| strings within 1 css px | 62% | 81% | 76% |

## 4. Glyph discrepancy report (v3 Regular)

| Glyph | IoU raw | IoU width-normalised | Width cand/ref (px) | Category | Observation |
|---|---|---|---|---|---|
| J | 0.44 | 0.62 | 28/31 | Structural | Pinterest J has a wider hook and heavier terminal; Instrument J is narrower (clamped at +8% scale). |
| K | 0.63 | 0.63 | 37/37 | Structural | Arm/leg junction sits at a different height and angle. |
| Q | 0.71 | 0.71 | 51/51 | Structural | Reference tail is a diagonal stroke crossing the bowl, dropping 5 px below the baseline; Instrument tail is short and nearly horizontal (1 px). |
| i | 0.71 | 0.83 | 7/8 | Proportional | Dot and stem are 1 px narrower than the 8 px reference; small-glyph pixel sensitivity. |
| R | 0.74 | 0.74 | 35/35 | Structural | Bowl closes higher in the reference; leg starts differently. |
| a | 0.75 | 0.75 | 32/32 | Structural | Terminal and stem/bowl junction differ; tail flare. |
| y | 0.75 | 0.83 | 34/35 | Terminal | Reference tail ends in a flat-cut foot; Instrument tail curves. |
| Y | 0.76 | 0.87 | 40/41 | Proportional | Arms slightly narrower in the reference. |
| G | 0.77 | 0.79 | 45/46 | Structural | Reference has a spur dropping below the baseline; crossbar position differs. |
| g | 0.77 | 0.82 | 33/34 | Structural | Instrument g has an ear/spur at upper right; the reference does not. |
| C | 0.78 | 0.78 | 46/46 | Terminal | Reference terminals cut vertically; Instrument cuts at an angle. |
| r | 0.80 | 0.91 | 20/18 | Proportional | Arm 2 px wider than reference. |
| c | 0.80 | 0.80 | 33/33 | Terminal | Terminal cut and aperture differ. |
| j | 0.81 | 0.81 | 14/14 | Terminal | Tail terminal differs. |

Stroke differences (A-F classification): **Proportional** residuals are small after the width edit (mean 4.0% MAPE; the largest remaining are 8-10 px punctuation: `.` `,` `:` `;` `!` are 20-27% narrower than the reference, `-` 26% and `)` 25% wider). **Structural** differences (Q tail, J, K, R, a, g, G) need outline redesign that cannot be validated beyond the screenshot and were **not** edited. **Spacing** differences are at the sub-pixel pair level (section 7). **Optical** equivalence is not claimed.

## 5. Weight validation (genuine masters)

| File | CSS weight / OS/2 class | Instrument wght axis | Ellipse thickening (ex, ey units) | Measured vs target stems (within 5%) | Confidence |
|---|---|---|---|---|---|
| SynthetixUI-Regular.ttf/.woff | 400 / 400 | 422 | 4.5, 14.0 | 10/11 (H 6.22, n 6.06, E arms 5.99 px) | Regular: HIGH targets; heavier: MEDIUM (lc stem 7.26/8.96 px) + LOW (other strokes assumed to scale) |
| SynthetixUI-Medium.ttf/.woff | 500 / 500 | 519 | 2.5, 18.3 | 11/11 (H 7.46, n 7.45, E arms 7.25 px) | Regular: HIGH targets; heavier: MEDIUM (lc stem 7.26/8.96 px) + LOW (other strokes assumed to scale) |
| SynthetixUI-SemiBold.ttf/.woff | 600 / 600 | 635 | 0.0, 27.3 | 11/11 (H 9.26, n 9.08, E arms 8.91 px) | Regular: HIGH targets; heavier: MEDIUM (lc stem 7.26/8.96 px) + LOW (other strokes assumed to scale) |

Proof each weight is a real resource: three distinct files with distinct outlines (different measured stems above), `usWeightClass` 400/500/600, name IDs 1/2/16/17 consistent, loaded as three separate `FontFace` objects in Chromium, and the browser test confirms `font-weight:300` uses 400, `700` and `900` use the 600 face with **identical** widths (no synthetic bold), and 400 < 500 < 600 widths. There is **no Bold 700 master**; none is supported by the evidence. Weight masters are interpolated from Instrument Sans' own Regular and Bold masters (OFL) and then calibrated; horizontal strokes are thickened with an elliptical offset so the horizontal/vertical stroke ratio matches the report (E arms/H stem 0.98, report 0.98).

## 6. Engineering changes, by iteration (kept or reverted on evidence)

| Iteration | Change | Result / decision |
|---|---|---|
| 1 Audit | No changes. Baseline measured for plain Instrument Sans and v2. | Baseline score 29.2 / 43.1. |
| 2a Grid and vertical metrics | Rescaled to UPM 1000 (outline scale 0.9718) so cap = 700; per-class vertical remap: x-height 500, ascender 729 (b d f h k l), descenders 171 (p q y) / 186 (g j), digits = cap. Vertical metrics pass 8/9 (Q tail only). | KEPT. Ascender 49->51 px, descenders 14/15->12/13 px matched. |
| 2b Glyph widths | Per-glyph centred width scale from the report W (HIGH) after correcting a 0.15 px threshold-box bias, clamped to +-10% (J, E, K, R, t hit the clamp), 54 glyphs, sidebearings preserved (advance grows with ink). | KEPT. Width MAPE 7.76% -> 4.0%; glyphs within 1 px 30 -> 68 of 79. An earlier variant that scaled about the left edge and moved advances was REVERTED (worse held-out spacing). |
| 3 Weights and strokes | Three masters calibrated by Nelder-Mead on 11 stem measurements (vertical + horizontal) at cap 49 px; ellipse-offset thickening separates horizontal from vertical stroke weight. | KEPT. Regular stems within 5% on 9/11 (plain 0/11, v2 2/11); E arms 5.0 -> 6.0 px. |
| 4a Spacing: global tracking | v2 global tracking removed. A uniform +13-unit sidebearing was first tried (leave-one-pair-out RMS 1.40 vs 1.66) and then REPLACED, because the deficit was caused by width scaling and thickening shrinking sidebearings; preserving each glyph's original sidebearings makes the constant unnecessary. | KEPT (sidebearing preservation). Pair-gap RMS 1.89 (v2) -> 1.09 px. |
| 4b Spacing: classes | A 16-parameter edge-class sidebearing model fitted on pair gaps: leave-one-pair-out RMS 1.57 vs 1.66 untuned. | REVERTED (overfits; per-glyph models also lost to doing nothing). |
| 4c Word space and kerning | Word space set to 214 units (report MEDIUM; measured deficit 2.7 px); pair kerning exceptions where residual >= 2.5 px added to the GPOS kern lookup (digit pairs 1-2, 5-6). | KEPT. Space gaps within 1 px: 5/6; strings within 1% of reference ink width. |
| 5 Geometry | No outline redesign. Ellipse emboldening and width scaling raised mean IoU 0.78 -> 0.855; 31/52 glyphs pass 0.85. | Structural fixes (Q tail, J, K, g, G) deferred: not validatable beyond screenshot pixels. |
| 5b Coverage | Added U+20A6 (Naira) constructed from N plus two horizontal bars at stroke-matched thickness (not measured against any reference). | KEPT as coverage, unscored for fidelity. |
| 6 Browser testing | 8 Chromium tests (section 8). | All pass; Firefox/WebKit unavailable. |
| 7 Regression | Rerun of every metric on the final files; names, license, metrics, hinting and composite checks (9/9). | No regressions in vertical metrics; pangram word-gap RMS 0.98 vs plain 0.85 (small regression). |

## 7. Spacing and kerning

Alphabet+digit pair gaps (49 pairs): RMS 1.09 px, signed -0.04 px, 40/49 within 1 px. Sidebearings are the original Instrument Sans values; no letter-spacing is applied anywhere. Only two pair exceptions were needed (digit pairs). **Not measured:** AV, AW, AT, FA, LT, To, Ta, Te, Yo, Wa, Wo, VA and punctuation pairs have no reference gaps in the report, so their spacing is inherited from Instrument Sans' kerning and is unvalidated against Pinterest. All-caps runs: A-Z total ink 1203 px vs 1207 (within 0.5%).

## 8. Real-browser validation (Chromium 141 only)

| Test | Result |
|---|---|
| Font loading (3 faces) | SX 400 loaded; SX 500 loaded; SX 600 loaded |
| Weights 300/400/500/600/700/900 widths at 32 px (px) | 300: 440.0, 400: 440.0, 500: 444.2, 600: 450.3, 700: 450.3, 900: 450.3 -> no synthetic bold: True |
| Linearity across 12,14,16,18,20,24,32,48 px (max spread) | 400: 0.01%, 500: 0.01%, 600: 0.01% (pass < 0.6%) |
| Kerning active (AVATAR To Wa Yo VA, 32 px) | 306.3 px with kerning vs 332.7 px without |
| DPR 1/2/3 css widths | 1: 205.83, 2: 205.83, 3: 205.83 |
| Wrapping in 320 px at 14/16/18 px (lines, overflow) | 14px: 3 lines, overflow False, 16px: 4 lines, overflow False, 18px: 4 lines, overflow False |
| Line box, line-height normal at 100 px | 120 px (1.20 em as specified) |
| U+20A6 renders as a real glyph | ink 2466 px vs N 1895 px, notdef 1836 px -> True |
| Fallback when font file missing | widths 290.6 = 290.6 px -> True |

Not tested: Android Chrome hardware, Safari, Firefox (engines not installed), Windows rendering. Screenshots: `screens/sizes_weights.png`, `screens/v3_worst_overlay.png`.

## 9. Scoring (100-point rubric)

| Category | Max | Initial (v2) | Final (v3) | Evidence | Remaining discrepancy | Confidence |
|---|---|---|---|---|---|---|
| Glyph geometry and structural fidelity | 25 | 9.6 | 14.9 | 31/52 glyphs IoU>=0.85 (25 x fraction) | Structural glyph differences (section 4) | Medium: depends on screenshot-derived reference |
| Character-width accuracy | 15 | 9.9 | 12.9 | 68/79 glyphs within 1 px | 8-10 px punctuation, J, i, r | High (HIGH-class data) |
| Vertical proportions | 10 | 8.9 | 8.9 | 8/9 metrics within 1 px | Q tail depth | High |
| Stroke and weight accuracy | 15 | 1.4 | 9.9 | Regular 9/11 stems within 5% (50%); Medium 11/11, SemiBold 11/11 vs inferred targets at half credit (25%) | e crossbar +9%, n +4%; heavier masters validated only against LOW-confidence extrapolations | Medium (Regular) / Low (heavier) |
| Kerning and spacing | 15 | 7.9 | 12.8 | pairs 40/49, spaces 5/6, strings within 1% 4/4, held-out UI strings within 1 px 76% | Named kerning pairs unmeasured; pangram word-gap RMS 0.98 vs plain 0.85 | Medium |
| Optical appearance and rendering | 10 | 0.0 | 5.0 | 8/8 Chromium tests (5 pts); no other engine, no expert optical review scored | Firefox/Safari/device untested; optical equivalence not scored | Medium |
| Unicode coverage and font integrity | 5 | 3.7 | 4.4 | integrity 9/9, 8 of 27 test symbols still missing | No check mark, euro-adjacent symbols, math symbols | High |
| Technical implementation | 5 | 1.7 | 3.3 | TTF+WOFF, honest weight mapping, no CSS hacks, reproducible scripts | No WOFF2 (no brotli here); GitHub repo not updated this round | High |
| **TOTAL** | 100 | **43.1** | **72.1** |  |  |  |

Note: v2 initial 0.0 for optical/rendering means *not tested*, not failed. Stroke credit for the Medium and SemiBold masters is capped at half because their targets are inferred (LOW/MEDIUM), and they were calibrated to those same targets. Rubric formulas: geometry = 25 x (glyphs with IoU >= 0.85)/52; width = 15 x (glyphs within 1 px)/79; vertical = 10 x (metrics within 1 px)/9; stroke = 15 x [0.5 x Regular pass + 0.25 x 0.5 x Medium pass + 0.25 x 0.5 x SemiBold pass]; spacing = 15 x mean(pair gaps, word spaces, string widths within 1%, held-out UI strings within 1 css px); rendering = 5 x (Chromium tests passed); coverage/integrity = 5 x mean(symbols present, integrity checks passed).

## 10. Classification of statements
- **Measured facts:** all numbers in sections 2-9.
- **Visual judgments:** the glyph observations in section 4 (made from overlays) and the statement that the SemiBold counters stay open.
- **Assumptions:** 4.5 px/css-px scale, cap/em 0.70 grid, Medium/SemiBold horizontal-stroke ratios, 214-unit space (MEDIUM), the 600 weight class for the headline cut.

## 11. Why 9/10 was not reached, and what is missing

Reaching 90/100 needs +17.9 points. Points not earned (27.9 of 100): glyph geometry and structural fidelity 10.1, character-width accuracy 2.1, vertical proportions 1.1, stroke and weight accuracy 5.1, kerning and spacing 2.2, optical appearance and rendering 5.0, unicode coverage and font integrity 0.6, technical implementation 1.7. Closing the gap needs: (1) outline redesign of about 20 glyphs with reference bitmaps at several sizes (Q, J, K, R, a, g, G, y, C...) validated per glyph; (2) Medium and SemiBold pangram screenshots (horizontal strokes, widths, gaps) to replace the LOW-confidence extrapolations; (3) measured data for the named kerning pairs; (4) Firefox, Safari and real-device Android Chrome runs; (5) the app's real font identity (the Gestalt docs say system fonts); (6) WOFF2 tooling (brotli). Without (1)-(3) a verified 9/10 is not attainable from the supplied reference.

## 12. Reproduction
`tools/` holds every script; `data/` holds the parsed reference and calibration results. Order: parse_report.py, verify_report.py, audit_html.py, audit_fonts.py, v3/calibrate.py (per master), v3/widths.py, v3/final_build.py, v3/eval_final.py, v3/final_checks.py, v3/browser_tests.py, v3/make_scores.py. Requires fonttools, playwright+chromium, pillow, numpy, scipy.
