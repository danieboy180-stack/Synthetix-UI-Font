# Synthetix UI (v2)

A tuned fork of **Instrument Sans** (SIL OFL 1.1) that mimics the proportions, weights and spacing measured from Pinterest's in-app UI type. It copies no Pinterest font data and is not affiliated with Pinterest. Glyph outlines are Instrument Sans's, edited only for proportions.

## Honest score
| Dimension | Result | Score |
|---|---|---|
| Weight match | stem/cap within 1.3% (wght 420 / 500 / 610 cut from the true masters) | 9/10 |
| Vertical proportions | ascenders, descenders, i/j dots, x-height, caps within 0.6% of cap height | 9/10 |
| Letter widths | mean error 0.011 cap (was 0.032); worst J 0.085 | 8.5/10 |
| String spacing, held-out | 0.97 css px, leave-one-text-out over 20 texts (plain Instrument Sans 1.19) | 8.5/10 |
| Real-browser widths | 0.98% mean error over 41 strings (plain 1.62%) | 8.5/10 |
| Glyph shapes | outlines are Instrument Sans's: g, a, t, J, stroke ends differ | 6/10 |
| Coverage | 52 letters at 3 sizes; digits and punctuation measured but not edited; Medium, bold pangram, small sizes not measured | 7/10 |

**Overall: 8/10 as a stand-in, 5.5/10 against "identical".** A true 10/10 would need Pinterest's licensed outlines.

## What v2 changed
1. **Data:** pangram (A-Z, a-z, 0-9, punctuation) at three display sizes, plus 28 menu strings at three sizes. Vertical ratios agree across sizes: x-height/cap 0.715, ascender/cap 1.04, descender/cap 0.24.
2. **Proportion edits** (`tools/tune_glyphs.py`, table in `tools/fork_params.json`): 24 letters' widths scaled within +-8% about the ink centre with advances unchanged; ascenders +4.0% cap (b d f h k l); i/j dots +2%; descenders p q -4.6%, g j -4.9%, y -2.9%.
3. **Tracking** refit on edited fonts: +14 / +11 / +7 units per 1000 em (Regular / SemiBold / Bold). **Size:** `size-adjust:108%`, cap-matched (font px = cap / 0.72), so 16px = measured body.
4. **What failed (and was not shipped):** scaling about the left edge and moving advances made held-out spacing worse (1.15 vs 1.08 css px); per-glyph advance and side-bearing fits overfit and lost to doing nothing.

## Use it
```html
<link rel="stylesheet" href="css/synthetix-ui-font.css">
<p class="sx-body">Body</p>  <p class="sx-label">Row label</p>  <h1 class="sx-h1">Headline</h1>
```
or `font-family:"Synthetix UI"; font-size:16px; font-weight:400|600|700`. No letter-spacing needed. Needs Chrome/Edge/Firefox 92+ or Safari 17+ for `size-adjust`. Native apps (no `size-adjust`): multiply sizes by 1.08.

## Files
`fonts/` (see below), `css/synthetix-ui-font.css`, `tools/build_fork.py` + `tune_glyphs.py` + `fork_params.json` (the calculations), `tools/browser_fit.py` (fit and verify in Chromium), `tools/fit_font.py` (ranks proportions; ignore its spacing output), `metrics/pinterest-sans-measured.json`, `preview/index.html`.

## Getting the fonts
Font binaries cannot be pushed through the tooling used here. Upload the six files from the chat download into `fonts/` and check them against `fonts/SHA256SUMS.txt`, or rebuild (not byte-identical, timestamps differ):
```
pip install fonttools
python tools/build_fork.py --regular InstrumentSans-Regular.ttf --bold InstrumentSans-Bold.ttf --out fonts
python tools/browser_fit.py verify --fonts fonts --plain-regular InstrumentSans-Regular.ttf --plain-bold InstrumentSans-Bold.ttf
```
Inputs: https://github.com/Instrument/instrument-sans.

## Known limits
- All-caps runs are about 2-3% wide (tracking was fitted on mixed-case UI text).
- J stays about 8% narrower than Pinterest's (edit capped at +-8%); Q tail depth, punctuation sizes and digits are unedited.
- Accented glyphs follow the base glyph's advance, but GPOS mark anchors were not updated.
- Pangram text came from a bio field; tracking in other contexts was checked only on menu and label text.
- Whether the app UI really uses Pinterest Sans is unconfirmed (Gestalt says system fonts); the UI digit "0" does not match the phone's status-bar "0" (0.78 overlap).
- Medium weight, small sizes and a second device remain untested; other base fonts (Figtree, DM Sans, ...) were not tested for lack of network access.

## Licence
Modified Version of Instrument Sans under the SIL OFL 1.1 (`fonts/OFL.txt`). Copyright 2022 The Instrument Sans Project Authors. Renamed; the original declares no Reserved Font Name. Do not sell the fonts by themselves.
