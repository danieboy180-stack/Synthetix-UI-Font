# Provenance register
- VERIFIED: V4 pipeline (regression, checks, confusables, engine parity, contract) re-ran in the build sandbox; 92-glyph coverage, no .notdef, no empty glyphs; metrics table; VF reproduces masters (bbox ≤0.7u, area ≤0.33%); Chromium loads font, axis changes widths 370/395/407 px, ₦ column right edges equal; fit error ≤1.42u for 300–500.
- MEASURED (historical, not V5): screenshot ratios from V4 reference JSON. **Label problem found:** the table rows "O width / cap" and "n width / cap" equal lowercase o and n widths divided by **x-height** (o 41.5px/xh 41px ≈ 1.01; n 36/41 ≈ 0.88) — relative to cap (56px) they would be 0.74 and 0.64. Re-check against the JSON before using.
- INFERRED: stress/contrast, sidebearing classes, aperture logic, tabular-default figures.
- PROPOSED: every V5 design number, direction A, thresholds in V5_CONTRACT.md.
- UNKNOWN: x-height optimum; native-reader acceptance; Windows/macOS/Android/iOS rendering; kerning needs; licensing/trademark; commercial viability.
- External fact: Pinterest Sans is a proprietary typeface commissioned from Grilli Type (public press coverage) → outlines unavailable and must never be copied.
