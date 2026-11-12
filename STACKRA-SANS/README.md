# Stackra Sans (V5) — working build 0.5.0-dev

Independent typeface, drawn from scratch in code (skeleton + variable-width stroker + own overlap remover). **No V3/V4 outlines, no Instrument Sans, no Pinterest outlines are used.** V4 (repo root) is research input only.

**Status: working prototype, NOT release-ready, NOT 10/10.** See `SCORECARD.md` for gate status and `GLYPH_STATUS.md` for coverage.

## What is in this branch
Source code (`build/scripts/`), docs, QA reports (`reports/`), interactive specimen page (`specimens/index.html`).
**Not committed here:** font binaries (TTF/WOFF), UFO sources, PNG specimens — they are in the hand-off `STACKRA-SANS-v5.zip`. UFO sources, static TTFs, WOFF and checksums regenerate with `build/scripts/export_family.py`. The specimen page expects `../fonts/variable/StackraSans-VF.ttf` (produced by `varbuild.py`).

## What exists (all VERIFIED by running it in the build sandbox)
- 92 glyphs: A–Z, a–z, 0–9, core punctuation, curly quotes, ʼ (U+02BC), ₦ (U+20A6), dashes, brackets.
- Variable TTF, axis wght 300–500 (3 masters, harmonised).
- Static Light 300 / Regular 400 / Medium 500 (SemiBold/Bold generated but marked EXPERIMENTAL-NOT-VALIDATED: they have broken glyphs).

## Build
`pip install -r build/requirements.txt` then `bash build/build_all.sh` (fontTools, numpy, scipy, Pillow; offline-capable). Code: `geom.py` strokes/arcs, `boolop.py` overlap removal, `glyphs_lc.py` / `glyphs_uc.py` drawings, `glyphset.py` registry, `harmonize.py`, `varbuild.py`, QA scripts.

## Not built (explicitly)
African-language letters (Ɓɓ Ɗɗ Ƙƙ Ƴƴ Ɛɛ Ɔɔ Ẹẹ Ọọ Ṣṣ Ị Ụ Ǹ Ḿ Ṅ …), all combining marks/anchors/GPOS mark, kerning, every OpenType feature (tabular figures are the default; nothing switchable), proportional/oldstyle figures, fractions, most symbols (& @ # $ % € £ ₵ ₹), SemiBold/Bold, opsz, WOFF2 (brotli missing offline), Fontspector/FontBakery, native-OS tests, human review, legal review.
