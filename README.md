# Synthetix UI — V4.0.10 release candidate

> **Checkout note.** If `fonts/` and `tools/` are missing, this is the documentation-and-configuration commit. The complete tree (fonts, build, tools, tokens, UI kit) is `synthetix-ui-v4.zip`; unzip it over this checkout and commit. Binary fonts cannot be pushed through the connector used for this commit.

An OFL-licensed UI sans built on [Instrument Sans](https://github.com/Instrument/instrument-sans), tuned toward a Pinterest-style UI voice
(measured widths, proportions, three engineered weights) and extended for Nigerian-market products (Hausa, Yoruba, Igbo, tabular ₦ amounts).
Not affiliated with Pinterest. **Status: release candidate. This is NOT a 10/10 build** — see `reports/CONTRACT_STATUS.md`.

## What is in V4.0.10
- 626 glyphs / 450 encoded characters per master (V3: 502 / 344). **No V3 glyph outline or advance was changed** (485 byte-identical; the 17 tabular-figure glyphs were only re-centred to one exact width) — proven by `tools/check_regression.py`.
- **Pri-African Latin**: Ɓ ɓ Ɗ ɗ Ƙ ƙ Ƴ ƴ · Ẹ ẹ Ọ ọ Ṣ ṣ Ị ị Ụ ụ · Ɛ ɛ Ɔ ɔ · Ǹ ǹ Ḿ ḿ Ṅ ṅ · ʼ · combining dot below (U+0323) with working tone-mark stacking.
  Decomposed, precomposed and reversed-mark-order text render pixel-identically (192 Chromium comparisons).
- **Numerals**: exactly equal tabular figures (`tnum`), slashed zero (`zero`), `lnum`, `frac`, `numr`/`dnom`, `sups`/`subs`/`sinf`, ¼ ½ ¾ ⅓ ⅔ ⅛, ¹²³, ⁰–⁹, ₀–₉.
- **UI symbols**: ✓ № ± ≠ ≤ ≥ ≈ ∞ ₵ ₹ ⁄ and the Latin-1/Latin Ext-A gaps (Ĉ Ĝ Ĥ Ĵ Ŝ Ĕ Ĭ Ŏ Ĩ Ũ Ţ Ŧ Ŀ ŉ ĸ …).
- **Opt-in `ss13`** (tailed l, serifed I, looser rn/cl/vv) for IDs/codes; with `zero` it separates Il1, O0, rn/m, cl/d and vv/w at 12–14 px (the default text still fails I~l and rn~m).
- **Variable font** `SynthetixUI[wght].ttf` (wght 400–600, three masters, STAT + named instances); static 400/500/600; WOFF, WOFF2; unicode-range subsets (latin, latin-ext, african, symbols). The full variable latin subset is 50,192 B (over its 45,000 B budget); `css/synthetix-ui-lite.css` uses a 40,128 B lite subset (core features + ss13, no stylistic sets/frac).
- **Reproducible**: all 28 shipped font files rebuild byte-identically from a clean copy of the inputs.
- Design tokens (W3C JSON → CSS, Swift, Android), WCAG-checked palette, UI kit, wordmark outlines, QA tooling, CI workflow.
- Fixed an inherited V3 defect: `usWinDescent` was 300 while comma-below reached −329 in SemiBold (clipping on Windows).

## Use
```html
<link rel="stylesheet" href="css/synthetix-ui.css">   <!-- variable, 400-600 -->
<link rel="stylesheet" href="tokens/dist/tokens.css">
<p class="sx-body">Ẹ káàbọ̀ — ₦18,050.00</p>
<span class="sx-id">I1l0O-8B6</span>   <!-- ss13 + zero + tnum for IDs and codes -->
```
Use `css/synthetix-ui-static.css` for the three static weights. Fonts: `fonts/{ttf,woff,woff2,variable,subsets}`; checksums in `fonts/SHA256SUMS.txt`.

## Build and verify
```
pip install -r requirements.txt
python build/build_static.py            # 3 masters from baseline/v3 (frozen binaries)
python build/build_variable_export.py   # variable font, WOFF/WOFF2, subsets, SHA256SUMS
python tokens/build_tokens.py           # tokens, CSS, contrast report
python tools/check_regression.py && python tools/run_checks.py && python tools/check_reproducible.py
python tools/scorer/run_scorer.py fonts/ttf/SynthetixUI-Regular.ttf 400 reports/scorer/v4_Regular.json
python tools/confusables.py && python tools/engine_parity.py chromium && python tools/contract_check.py
```
WOFF2 needs the `brotli` wheel; where it cannot be installed `tools/brotli_node_shim` (Node's zlib brotli) is used — WOFF2 hashes then depend on that compressor build.

## Honest limits
Built in an offline sandbox: no Font Bakery, no Firefox/WebKit, no devices, no reference screenshots, no upstream Instrument Sans sources.
Everything not measured is marked NOT MEASURED in `reports/CONTRACT_STATUS.md`; nothing is estimated. New glyph designs (hooks, Ɛ/ɛ, ₹, ✓, ∞, ss13) are constructed and **unreviewed by a type designer**.
The name "Synthetix" collides with an established DeFi protocol — read `NAME_CLEARANCE.md` before any public use. License: SIL OFL 1.1 (`fonts/OFL.txt`), Instrument Sans copyright retained.
