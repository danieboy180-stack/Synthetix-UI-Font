# Synthetix UI Font

Open-source stand-in tuned to measurements of Pinterest's in-app UI type (Android app + mobile web), built from screenshots.
Base font: **Instrument Sans** (SIL OFL). Nothing here contains Pinterest font files or traced outlines.

## Honest score
| Dimension | Result | Score |
|---|---|---|
| Vertical proportions (x-height, ascender, round "o", "n") | within 3.5% of target; descenders 15-20% too long | 8/10 |
| Real-browser widths (Chromium, 4.5x) | -0.5% to +1.8% on 3 strings | 8/10 |
| Glyph spacing, **held-out** (leave-one-out) | Regular 0.91 css px, Semibold 0.74 (untuned: 1.24 / 1.83). Bold not testable (1 sample) | 7/10 |
| Weight match | Regular stem -5%; Semibold/Bold use interpolated wght 500/610, untested on a variable file | 6/10 |
| Glyph shapes | 0.77 overlap (IoU); g tail, t cut, terminals differ | 5/10 |
| Coverage | ~20 lowercase letters, 4 digit widths, few capitals | 4/10 |

**Overall: 7/10 as a stand-in, 5/10 against "100% identical".** The earlier "0.65 css px" figure was in-sample; the held-out figure is 0.91.

## Research findings
- **Pinterest Sans** was designed by Grilli Type with Made Thought (announced 2021). Press coverage describes a taller x-height in every weight, vertically cut stroke endings, and a mix of geometric and handwritten character. My measured x-height/cap of 0.73 fits that description.
- **Conflict:** Pinterest's public design system (github.com/pinterest/gestalt, typography page) says product UI defaults to system fonts and Pinterest Sans is for branded graphics, "never for UI". That page may be stale or may describe only parts of the product.
- **Test:** the UI "0" matches the phone's own status-bar "0" at only 0.78 IoU (same-font control = 1.0, a plain Arial-like "0" = 0.91). So these screenshots are **not** in the phone's system font. They most likely show a Pinterest-supplied face, but I could not confirm which.
- `pinterest.com` blocks automated access, so its CSS and font files were not inspected. To confirm yourself: open the site, DevTools > Elements > Computed > "Rendered Fonts".

## Measured spec (css px = screenshot px / 4.5)
Scale checks: 48 css button = 216 px; 16 dp margin = 72 px; card width 1440 px = 320 css px.

| Role | cap | x-height | ascender | baseline pitch | stem/cap |
|---|---|---|---|---|---|
| Body | 12.44 | 9.11 | 12.9 | 24.67 | 0.117 |
| Semibold rows | 12.44 | 9.11 | 12.9 | n/a | 0.143 |
| Web H1 | 15.78 | 11.56 | 16.44 | 31.56 | 0.179 |

Scale-free: x-height/cap 0.73, ascender/cap 1.03-1.04, descender/cap 0.23-0.27, "o" width/x-height 1.00-1.02, digits lining and proportional ("1" = 0.43 cap).
All raw data: `metrics/pinterest-sans-measured.json`.

## Candidates tested (12 fonts available offline)
Instrument Sans was the best balance (regular IoU 0.765). Adventor fit proportions but has the wrong single-story a. Carlito was too narrow, Liberation Sans too narrow in "o", Poppins and Work Sans off in x-height or width.
Not tested (no network): Figtree, DM Sans, Plus Jakarta Sans, Albert Sans, Hanken Grotesk, Onest, Inter.

## Use it
- `css/synthetix-ui-font.css`: tokens and classes. Values marked PROVISIONAL were solved on static 400/700 files.
- `python tools/fit_font.py --font <file> ...`: ranks any font against the measurements and emits CSS numbers (sweeps `wght` on variable fonts).
- `python tools/loo_validate.py --regular R.ttf --bold B.ttf`: held-out accuracy.
- `python tools/browser_check.py --regular R.ttf --bold B.ttf`: real Chromium render check (needs playwright).
- `preview/index.html`: live specimen.

## What cannot reach 10/10 here
1. **Glyph outlines:** identical shapes need the licensed font. Redrawing it from screenshots is copying it. An original face drawn to this spec is the only legitimate route to full metric parity.
2. **Coverage:** every missing glyph needs more screenshots (all digits, A-Z, punctuation, Medium weight, 12-14 px sizes).
3. **Variable-weight tracking:** Semibold/Bold spacing must be re-fitted on the real variable file.
4. **Candidate search:** run `fit_font.py` on the untested fonts above.
5. **Single device:** one phone, one renderer; a second capture would test the 4.5 scale assumption.
