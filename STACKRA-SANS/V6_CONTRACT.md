# Stackra Sans V6: contract

Source of truth for every number is `build/scripts/contract.py`; this page explains it. Status of the 200 requested steps is in
`v6_ledger.json` and (regenerated each build) `RELEASE_READINESS.md`.

## What this branch is
A hardened build of the V5 engine plus named geometry repairs (`build/scripts/glyphs_v6.py`). It is not a redesign: the
glyph drawings, spacing formulas and coverage (92 glyphs, Latin basics + naira) are V5's except for `Y`, `bracketright`,
`greater`. Working family name `Stackra Sans` is not cleared (ledger A3/A96/A97). No licence or copyright text is embedded (A95).

## Gate tiers
| Tier | Effect | Gates |
|---|---|---|
| Integrity | build fails (non-zero exit) | glyph exceptions / empty outlines, contour + segment topology, per-weight validity, 23 QA gates (`qa_font.py`), dense interpolation (`interp_test.py`), negative self-tests (`selftest.py`) |
| Design (registered, may be open) | reported; fatal with `build_all.sh --release` | confusables @14 px (`confusables.py`): I/l currently fails (DECISIONS D-0004) |
| Human / legal | tracked in the ledger only | blockers A1-A4, A95-A98, native review, devices, licensing |

## Registered thresholds (see contract.py for the live values)
| Gate | Limit | Origin |
|---|---|---|
| Outline fit error | <= 1.5 units | carried from V5 |
| Interpolation area / bbox | <= 2 % / <= 2 units | carried |
| Interpolation advance | <= 2 units | V6, corrected from 1.0 (D-0007) |
| Dense sampling | every 25 wght units | V6 |
| VF vs static at public weights | bbox <= 1 unit | V6 |
| Boolean-engine raster mismatch | <= 5 % per call | V6, noise-floor calibrated (D-0006) |
| Confusables @14 px | I/l 0.60, l/1 0.30, O/0 0.45, rn/m 0.40, cl/d 0.45 | carried |
| Size budgets | VF TTF 60 KB, VF WOFF2 30 KB, static WOFF2 14 KB | V6, set before measuring |

## Commands
`bash build/build_all.sh` (dev) or `bash build/build_all.sh --release`; `bash build/repro_check.sh` for the double-build proof.
WOFF2 needs `brotli`; without it the report says NOT RUN (set `STACKRA_REQUIRE_WOFF2=1` to make that fatal).

## What these gates do not prove
Design quality, spacing or kerning quality (V5 has no kerning), language correctness (no Hausa/Yoruba/Igbo letters yet),
rendering on real devices or browsers, accessibility, legal status. A score of 9.9/10 cannot be claimed from this branch.
