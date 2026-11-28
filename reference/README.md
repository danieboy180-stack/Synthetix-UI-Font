# reference/ (plan step 26: versioned, never overwritten)

| id | crop (in repo) | private source name | source sha256 | crop box x0,y0,x1,y1 | text lines |
|---|---|---|---|---|---|
| A | reference/captures/pangram_A.png | Screenshot_20261031-125556_Pinterest.png | `69c41eab26fc3a0cb27d0953f725042f81e02034749285262524f585796f3938` | [0, 865, 1430, 1403] | 5 |
| B | reference/captures/pangram_B.png | Screenshot_20261031-125615_Pinterest.png | `61eb638c035da2ffebcde01bf133e006ac9eb9166038228743753059b88e8760` | [0, 805, 1440, 1189] | 4 |
| C | reference/captures/pangram_C.png | Screenshot_20261031-125641_Pinterest.png | `bd5038df97740e569d97a19d8ac5cddfa2533a4454942a6386a0c016a6bfbd52` | [0, 704, 1439, 1045] | 4 |

Captured 2026-10-31 (file names). Cropped and measured 2026-11-28 (session 1).

* `captures/` text-only crops of the pangram sheet + `captures.json` (line texts, hashes).
* `glyphs/` 334 per-glyph bitmaps (`u<HEX>_s<cap px>_<n>.png`, baseline row 166, cap row 38, cap = 128 px) + `index.json` + `overlay_*.png` for QA. Measurement crops only: never traced, never used as outlines.
* `dna/`, `split.json`, `pinterest-sans-measured.json`, `report_reference.json`, `v3-reports/` are the frozen V4 inputs (locked by `reports/scorer.lock.json`).
* `captures_private/` is git-ignored: raw screenshots live there only.
