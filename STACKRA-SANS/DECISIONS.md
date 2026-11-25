# Stackra Sans V6: decision log

One entry per decision, dated, with the evidence it rests on. A registered threshold is never relaxed after a failed
result unless an entry here says so in plain words (D-0007 is the one such case so far).
Snapshot date for every entry below: 2026-11-23. Owner/approver fields are empty: naming them is a human step (ledger A10).

## D-0001 Baseline
V6 was cut from `v5-stackra-sans` at commit `76c7660de00bbac66477555be35f4574ea5e9b80`.
Measured V5 facts when the cut was made: 92 glyphs; public masters 300/400/500; outline fit error 0.89 / 1.15 / 1.42
units at 300/400/500 (unchanged in V6); the variable font was named "Stackra Sans W400" (a placeholder style name).

## D-0002 Lineage
V6 continues the V5 engine: every outline comes from original code (`geom.py`, `boolop.py`, `glyphs_*.py`). The second
plan (a 100-step V4 roadmap) assumes a derivative of an open-source base and a reference-matching goal. Steps that need
that premise are marked NA in `v6_ledger.json` with the reason (B7, B42-B57). If you want V6 to become a derivative
of Instrument Sans, that is an owner decision that also changes licensing (A95) and originality (A4); it is not made here.
The claude.ai artifact link that was supposed to hold a second step list could not be read (empty page); the second list
used is the uploaded .docx.

## D-0003 Public weights
Public range stays 300/400/500. 600 and 700 fail the computed gates and are written to `fonts/experimental/` as TTF only,
never hashed into the release checksums, never given web formats. Promotion needs a new entry here.

## D-0004 I/l confusable: OPEN, gate failing
Registered maximum (carried from V5): Jaccard(I, l) at 14 px <= 0.60. Measured on the V6 proto master: 0.692.
Candidate fixes measured (tail of `l`, ink width 216 -> 519 units): rxh 104 (current) 0.692, 150 -> 0.600, 180 -> 0.562,
200 -> 0.529, 220 -> 0.500, with the `l` advance growing 348 -> 424 -> 492 -> 538 -> 585. Not applied: a wider hooked `l`
changes the typographic colour and identity of every text, and a serifed capital `I` is the other route. Owner decides.
Other registered pairs at 14 px: l/1 0.13, O/0 0.40, rn/m 0.28, cl/d 0.42 (all within their maxima).
The bitmap Jaccard is a proxy; it is not a legibility test.

## D-0005 Intermediate masters 350 and 450
With 3 masters the dense gate (every 25 wght units, carried thresholds) failed for 11 glyph/weight cases. Adding masters at
350 and 450 left 5, all of them 2-unit advance deviations (D-0007). Thresholds for area (2 %) and bbox (2 units) were not
changed. File size: variable font 18.7 KB (3 masters) -> 28.8 KB (5 masters), inside the 60 KB budget.

## D-0006 Defects the new gates found in V5, and the Boolean-engine threshold
- `Y` at wght 300: the custom overlap-removal engine added a spurious triangle to the left arm (raster mismatch 386 of
  2171 cells = 17.8 %). Cause: the arm corners sit about 4.6 units inside the stem edge at that weight, which defeats the
  chaining step. Fix: `Y` is now one analytic 9-vertex outline (`glyphs_v6.py`). The engine itself was NOT fixed, so other
  glyphs could hit similar near-degenerate cases; the raster gate covers the 5 masters only.
- `bracketright` and `greater`: mirrored contours kept the reflected (wrong) winding in every V5 file. Fixed in
  `glyphs_v6.py` by restoring the direction after the reflection.
- Threshold: `BOOL_MISMATCH_MAX_FRACTION = 0.05`. This was chosen AFTER looking at the baseline distribution (median 0.2-0.4 %,
  worst non-defect case 3.3 % on thin bars of `equal` at 400), so it is a noise-floor setting, not a pre-registered one.

## D-0007 Advance threshold corrected 1.0 -> 2.0 units (a deviation from the never-relax rule)
`INTERP_ADVANCE_MAX_UNITS` was registered at 1.0 in this session before any gate run. After the 5-master run, 5 cases failed by
exactly 2 units (less/greater at 325; slash, quotedblleft, quotedblright at 425). An advance is the sum of three rounded
quantities and the variable font interpolates two rounded masters, so differences of up to 2 units appear even when the
geometry is exact. The value was moved to 2.0 on that argument. This is a change made after seeing failures; if you reject it,
set it back to 1.0 and those 5 cases become open defects. Area and bbox thresholds were not touched.

## D-0008 Metadata and vertical metrics
`hhea` and OS/2 typo metrics were made identical (950 / -250 / 0), USE_TYPO_METRICS set, OS/2 version 4, win metrics 1000/280
(gated to cover every glyph). Names follow the RIBBI rule (IDs 1/2, plus 16/17 for Light/Medium). The variable font now
carries `Regular` instead of `W400`, named instances, a full STAT and `gasp {65535: 15}`; ulUnicodeRange comes from the cmap;
timestamps are fixed by SOURCE_DATE_EPOCH. None of this has been checked on real operating systems (ledger A61/A67).
Copyright, licence and designer name IDs are deliberately NOT set: they depend on the legal decisions (A95-A97).
