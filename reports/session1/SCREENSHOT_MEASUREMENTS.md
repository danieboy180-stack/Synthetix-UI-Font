# Reference screenshot measurements (session 1, Phase B partial)

Source: `reference/captures/pangram_{A,B,C}.png` (text-only crops of the Pinterest bio-edit sheet at three system font sizes, Regular weight), measured by `tools/measure_captures.py`; font = `fonts/ttf/SynthetixUI-Regular.ttf` (V4 as shipped). **These are measurements, not scorer output.** The frozen scorer was not touched. Lengths are normalised by cap height; errors are in px at a 16 px font size (cap = 11.2 px).

## Scale and vertical proportions

| sheet | cap px | x-height/cap | ascender/cap | descender/cap |
|---|---|---|---|---|
| A | 56.01 | 0.7143 | 1.0357 | 0.2321 |
| B | 49.00 | 0.7143 | 1.0408 | 0.2449 |
| C | 44.01 | 0.7044 | 1.0453 | 0.2500 |
| **reference mean** | | 0.7110 (sd 0.0046) | 1.0406 (sd 0.0039) | 0.2423 (sd 0.0075) |
| **Synthetix** | | 0.7143 | 1.0414 | 0.2443 |

Vertical proportions agree to within 0.4% of cap height (0.1 px at 16 px).

## Weight: stems as a fraction of cap height (same code measures reference and font)

| stem | reference | Synthetix Regular | reference / Synthetix |
|---|---|---|---|
| E_arm_bottom | 0.1175 | 0.1168 | 1.007 |
| E_arm_top | 0.1160 | 0.1168 | 0.993 |
| O_sides | 0.1257 | 0.1346 | 0.934 |
| o_sides | 0.1209 | 0.1346 | 0.898 |
| o_top_bottom | 0.1114 | 0.1073 | 1.039 |
| stem_H | 0.1199 | 0.1344 | 0.892 |
| stem_I | 0.1157 | 0.1344 | 0.861 |
| stem_T | 0.1232 | 0.1208 | 1.020 |
| stem_l | 0.1099 | 0.1344 | 0.818 |
| z_bars | 0.1129 | 0.1168 | 0.967 |

Within 5%: 5 of 10 (E_arm_bottom, E_arm_top, o_top_bottom, stem_T, z_bars). Within 3%: 3 of 10 (E_arm_bottom, E_arm_top, stem_T).

**Monolinearity.** Reference vertical stems ≈ horizontal stems (V/H = 0.997). Synthetix Regular V/H = 1.135, Medium 1.079, SemiBold 1.040: it keeps Instrument Sans's stroke contrast, and its vertical stems are 16.6% heavier than the reference while horizontals are 2.5% heavier.

| weight axis (stem/cap, vertical) | Synthetix | reference class (frozen v2 measurement) |
|---|---|---|
| Regular | 0.1343 | regular 0.1173 (session-1 re-measure 0.1152) |
| Medium | 0.1573 | semibold 0.1434 |
| SemiBold | 0.1910 | bold 0.1786 |

Inside Medium and SemiBold the stems are not uniform across glyphs (stem H 0.1658 vs stem l 0.1429 in Medium; 0.2057 vs 0.1837 in SemiBold). The reference class values for semibold and bold are from the older, title-size measurement, not a same-method re-capture (needs plan steps 12 and 24).

## Glyph widths (ink width / cap, error in px at 16 px)

79 glyphs (letters, digits, punctuation): within 0.5 px **72** (91.1%), within 1 px **77** (97.5%), mean abs error 0.187 px. Measurement noise across the 3 sizes: sd 0.059 px.

Largest: `-` -1.33, `(` -1.09, `J` +0.73, `/` +0.72, `,` +0.62, `;` +0.57

## Ink-to-ink pair gaps (kerning applied through HarfBuzz)

106 adjacent pairs found in the pangram strings (NOT the held-out split): within 0.5 px 97, within 1 px 105, rms 0.336 px. Noise sd 0.067 px. Largest: `)/` -2.28, `-:` +0.79, `RS` +0.70, `()` +0.59, `ar` -0.57, `ab` -0.57

Line ink widths vary by up to ±2.7 px@16 between sheets for the same string (renderer rounds advances differently at each size), so whole-line tracking is not reliable evidence below about 2 px; per-pair gaps are.

## Shape IoU (provisional method, `tools/glyph_iou.py`)

Letters (52): median **0.828**, 41 below 0.88, 34 below 0.85; best-horizontal-shift bound: median 0.853, 36 below 0.88. All 79 glyphs: median 0.786. Lowest letters: `J` 0.35, `K` 0.55, `R` 0.66, `Y` 0.67, `y` 0.68, `a` 0.72, `k` 0.74, `v` 0.76, `G` 0.76, `C` 0.77. Heatmaps: `reports/diffs/`, ranking `reports/diffs/RANKING.md`.

Visible structural differences in the heatmaps: reference `3` has a flat top bar; `J` hook and `K` leg geometry differ; `/` and `)` strokes sit at different offsets. Heatmaps show where; the DNA specs (plan step 20) are still to write.

## Not covered by these captures

SemiBold/Bold/heading/big-digit sizes, dark mode, Hausa/Yoruba/Igbo text, letters in 3 words each, the 70/30 split. They are in `reports/NEEDS_FROM_DANIEL.md`.
