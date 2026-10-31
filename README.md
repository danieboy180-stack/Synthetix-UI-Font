# Synthetix UI

A tuned fork of **Instrument Sans** (SIL OFL 1.1) that mimics the proportions, weights and spacing measured from Pinterest's in-app UI type. It copies no Pinterest font data and is not affiliated with Pinterest. Glyph shapes are Instrument Sans's.

## Files
- `fonts/SynthetixUI-{Regular,SemiBold,Bold}.{ttf,woff}` and `fonts/OFL.txt` (font binaries: see "Getting the fonts" below)
- `css/synthetix-ui-font.css` tokens and classes
- `tools/build_fork.py` rebuilds the fonts from Instrument Sans; `tools/fork_params.json` holds the calculations
- `tools/browser_fit.py` fits and verifies in real Chromium
- `metrics/pinterest-sans-measured.json` the measurements; `preview/index.html` the specimen

## What was calculated
1. **Weights:** Regular and Bold masters become a variable font, then three weights are cut to hit the measured stem/cap ratios. Regular = wght 420 (stem/cap 0.116 vs 0.117), SemiBold = 500 (0.143 vs 0.143), Bold = 610 (0.178 vs 0.179). Plain Instrument Sans only has 400 and 700, so its bold is about 14% too heavy.
2. **Tracking:** fitted on glyph positions rendered in Chromium, `track(w) = +0.00422 - 0.01326 * (wght-420)/190` em, baked into advance widths: +4 / -1 / -9 units per 1000. Five other models were tested by leave-one-out and lost (word-spacing models overfit).
3. **Size:** `size-adjust:110%` so `16px` reproduces the measured body (cap 12.44 css px at 4.5 px/css-px). This assumes Pinterest's body is 16px; if it is not, only the nominal sizes change.

## Measured accuracy (9 strings, one device, real Chromium at 4.5x)
| | Synthetix UI | Plain Instrument Sans 400/700 |
|---|---|---|
| Mean glyph x-error | **0.81 css px** (0.97 held-out) | 2.09 |
| Mean width error | **0.95%** (worst +4.0%, "Settings") | 2.84% |

**Score: 7.5/10 as a stand-in, 5/10 against "identical".** Weights 9, spacing 8, widths 8, vertical proportions 8, glyph shapes 5 (0.77 overlap), coverage 4 (about 20 lowercase letters).

## Use it
```html
<link rel="stylesheet" href="css/synthetix-ui-font.css">
<p class="sx-body">Body</p>  <p class="sx-label">Row label</p>  <h1 class="sx-h1">Headline</h1>
```
or `font-family:"Synthetix UI"; font-size:16px; font-weight:400|600|700`. No letter-spacing needed. Needs Chrome/Edge/Firefox 92+ or Safari 17+ for `size-adjust`.

## Getting the fonts
Font binaries cannot be pushed through the tooling used to build this repo. Either upload the six files from the chat download into `fonts/` (GitHub: Add file > Upload files), or rebuild:
```
pip install fonttools
python tools/build_fork.py --regular InstrumentSans-Regular.ttf --bold InstrumentSans-Bold.ttf --out fonts
```
Inputs: https://github.com/Instrument/instrument-sans. WOFF2 needs the optional `brotli` package; WOFF is written by default.
Re-check the fit: `python tools/browser_fit.py verify --fonts fonts --plain-regular R.ttf --plain-bold B.ttf`.

## Corrections to earlier results
Earlier spacing numbers (held-out 0.91 / 0.74 css px, widths +1.3%) came from two flawed methods: Pillow ignores GPOS kerning, and default headless Chromium rounds glyph advances to whole css px. Both are replaced by `browser_fit.py` (subpixel positioning on). `tools/fit_font.py` is still useful for ranking proportions, but ignore its spacing output.

## Licence
Fonts are a Modified Version of Instrument Sans under the SIL OFL 1.1 (`fonts/OFL.txt`). Copyright 2022 The Instrument Sans Project Authors. Renamed; no Reserved Font Name is declared by the original. Do not sell the fonts by themselves.

## Limits
Identical outlines would need the licensed font. More coverage needs more screenshots (digits, A-Z, punctuation, Medium, small sizes). Medium weight and the 4.5 scale (assumed from the redline, cross-checked by a 16 dp margin) remain unverified.
