# V3 baseline audit (V4.0.0)

Date: 2026-11-07. Input: `synthetix-ui-v3.zip` (sha256 `e312c04a...efa4`, see `baseline/v3/BASELINE.md`). Tool: `tools/v4/audit_baseline.py` with fontTools 4.67.0.

Artifact: the audit's JSON output (15,855 bytes, not committed) has sha256 `e9274b1029f4a573d1d5e70cc019c2f990bbecc1a7399cbcf6aa780f09b2a03b`. Two runs were byte-identical. To regenerate and compare, after landing the baseline:

```
pip install fonttools==4.67.0
python tools/v4/audit_baseline.py --fonts baseline/v3/fonts --tools baseline/v3/tools --out /tmp/audit_v3.json
sha256sum /tmp/audit_v3.json
```

## V3 against the contract's hard gates

0 of 8 pass: 3 measured failures (H2, H3, H4), 1 unmet (H5), 2 not measurable (H1, H6), 1 blocked on the owner (H7), 1 undefined (H8).

| Gate | Status | Evidence |
|---|---|---|
| H1 Font Bakery | NOT RUN | Not installed, no network. Predicted risk: win-descent clipping in Medium and SemiBold (finding 1) |
| H2 Coverage | FAIL | Audit list: 5 of 31 Pri-African characters present; 8 of 21 UI symbols present. Latin Core not measured (no glyphset data offline) |
| H3 Tabular, .notdef | FAIL | tnum digit advances differ by 2 / 2 / 4 units (Regular / Medium / SemiBold); Naira not in tnum. .notdef exists with an outline; the required-character set is undefined (O-8) |
| H4 Reproducible build | FAIL | 16 of 18 scripts hardcode absolute paths; inputs are not hash-pinned (finding 2) |
| H5 Variable vs static | UNMET | No variable font (no fvar, avar, STAT) |
| H6 Cross-engine widths | NOT MEASURABLE | V3 report: Chromium 141 only |
| H7 OFL, name clearance | BLOCKED | Licence intact (below); name clearance open, collision confirmed (O-3) |
| H8 Critical defects | UNDEFINED | No severity definition (O-4) |

Licence, measured: name IDs 0, 13 and 14 present in all three files; OFL header copyright line is Instrument Sans's; no Reserved Font Name declared; fsType 0. Version string `Version 3.000; modified from Instrument Sans 1.000`. Vendor ID is the placeholder `NONE`.

## The plan's audit claims, re-checked on the V3 binaries

| Claim | Result |
|---|---|
| 7 priority glyphs already have alternates | Confirmed: Q.ss09, J.ss08, K.ss04, R.ss05, G.ss07, a.ss02, y.ss03 in all three weights; 111 `.ssNN` glyphs per font |
| Nigerian-language letters absent | Confirmed. Present: U+0300, U+0301, U+0304, U+014A, U+014B. Missing: U+0323; Hausa U+0181 U+0253 U+018A U+0257 U+0198 U+0199 U+01B3 U+01B4 U+02BC; Yoruba/Igbo U+1EB8 U+1EB9 U+1ECC U+1ECD U+1E62 U+1E63 U+1ECA U+1ECB U+1EE4 U+1EE5 U+1E44 U+1E45; U+0190 U+025B U+0186 U+0254 |
| Tabular digits not exactly tabular | Confirmed: Regular 587-589, Medium 585-587, SemiBold 583-587 |
| Number features thin | Confirmed: GSUB has tnum and pnum; no lnum, onum, frac, zero. Naira (advance 732 / 725 / 717) is not in tnum |
| Not reproducible | Confirmed and worse: 16 of 18 scripts, not 7 |
| No italic; 700 and 900 use the 600 face | Confirmed: no italic bit or angle; weights 400 / 500 / 600; the CSS sets `font-style: normal` and has no `font-synthesis` rule, so a browser would synthesize italic |

The code point lists are this audit's own (the plan names categories, not exact characters), so the counts are not the plan's "32 characters".

## New findings (not in the plan)

1. **Windows descent clipping.** Glyphs U+0122, U+0146, U+0326 and their alternates reach -308 (Medium) and -329 (SemiBold) against `usWinDescent` 300. Regular reaches -293 and is fine. Font Bakery was not run; a win-metrics failure is predicted, not observed.
2. **Input provenance.** Scripts read Instrument Sans from `/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSans-Regular.ttf` and `/home/claude/fork/IS-VF.ttf`. The upstream release, version and hash are not recorded.
3. **Alternates were not edited like the base glyphs** (resolves plan section 8, item 2 for widths and vertical remap; stroke thickening was not checked).
   - The 54 width factors are keyed by cmap characters; alternates are not in the cmap.
   - y.ss03 descends to -209 in all weights against -171 for base y (V3's remap target), so the descender remap was not applied. K.ss04, R.ss05 and J.ss08 reach 700 like their bases.
   - Q.ss09 tail reaches -125 / -135 / -145 (Regular / Medium / SemiBold) against -10 for base Q. V3's report puts the reference tail at 5 px below the baseline at cap 49 px, about 71 units. Bounding boxes only; no IoU, because the reference bitmaps are not in the zip.
4. **Link to the repo's v2.** `data/v2_embedded_Regular.woff` has the same sha256 as the v2 Regular WOFF in `main`'s `fonts/SHA256SUMS.txt`.
5. **Superseded v2 claims.** V3's report says v2's weight labels (400 / 600 / 700) did not match its cuts (wght 420 / 500 / 610) and scores v2 at 43.1/100 under its rubric, not "8/10". Taken from that report, not re-measured here. The v2 README on `main` should be read as superseded.

## V3 scores as recorded, not re-verified

V3 report: 72.1/100 under a blended rubric (weights 25 / 15 / 10 / 15 / 15 / 10 / 5 / 5), with geometry 14.9/25 and metric fidelity 44.5/55. They cannot be recomputed: the reference screenshots and bitmaps are not in the zip and the scorer scripts hardcode paths. The contract forbids blended scores, so these numbers are a historical record, not a V4 baseline (O-1, O-5).

## Not measured

Font Bakery; Latin Core (no gftools glyphset data offline); mark stacking and shaping (no shaper installed); cross-engine rendering; IoU and any other reference-based score; V3 build timestamps; the Naira shape (V3 constructed it, unscored).
