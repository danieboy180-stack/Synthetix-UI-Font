# Changelog (SemVer; font version = `head.fontRevision` = name ID 5)

## 4.0.10-rc.1 (font version 4.010) — release candidate, not a release
**Added** — 124 glyphs per master (450 encoded characters, V3: 344): Pri-African letters, U+0323, Latin Ext-A gaps, UI symbols, fractions/superscripts/subscripts, slashed zero,
`ss13`; features `lnum zero frac numr dnom sups subs sinf ss13`; variable font (wght 400–600) with STAT; WOFF2 + unicode-range subsets; design tokens; UI kit; QA tooling; CI workflow.
**Changed** — tabular figures set to exactly equal advance (see LAYOUT_STABILITY.md); `usWinDescent` 300 → 340 (all masters); version/name records.
**Fixed** — inherited V3 clipping of comma-below in Medium/SemiBold on Windows; `head.modified` wall-clock stamp in the variable build (found by the reproducibility check).
**Unchanged (proven)** — all 485 other V3 glyph outlines, advances and sidebearings; frozen-scorer results (widths 68/79, vertical 8/9, pair gaps 40/49, stems 9/11 on Regular).
**Known issues** — see `reports/CONTRACT_STATUS.md` and `V4_REPORT.md` (Q tail, J/K/R/a/C/G shape gaps, rn~m confusable, variable latin subset 51,232 B over its 45,000 B budget, name collision).

## Baseline
3.x (V3) frozen in `baseline/v3` with `SHA256SUMS.txt`.
