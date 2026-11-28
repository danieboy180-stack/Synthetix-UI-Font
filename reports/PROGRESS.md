# PROGRESS (session 1, 2026-11-28)

**Branch:** `phase-a-foundation` (local git history, 12 commits on top of main; not yet on GitHub, see Blockers).
**Current step:** Phase A complete (1-10; 5 and 9 partial). Phase B started (11, 16-18, 21-23, 26 partial). Phase C not started, by rule 5.
**Verdict:** partial, 28 evidenced of 100 points; 0 points earned. No total /100 and no likeness /10 are printed: Shape IoU, Stems (600/700) and String render have no accepted evidence.

## 1. Steps completed
| step | status | evidence |
|---|---|---|
| 1 unpack v4 over clean clone | done | commit `step 1`; scorer.lock 6/6 sha256 OK (`python tools/verify_scorer_lock.py`) |
| 2 Copilot + Claude instruction files | done | `CLAUDE.md`, `.github/copilot-instructions.md` (not tested inside Copilot/Claude Code) |
| 3 devcontainer + pins | written, not container-tested | `.devcontainer/`, `requirements-dev.txt` (pins `ufo-extractor`: PyPI `Extractor` is a different package) |
| 4 rebuild with real brotli | done | 28/28 files reproduce (`reports/reproducibility.json`); 626/626 glyphs identical to the V4 zip (`reports/session1/rebuild_equivalence.json`) |
| 5 CI | partial | old `ci.yml` was invalid YAML (line 20) and could never run; new one validated and every fast-job command run locally. **Not yet run on GitHub.** |
| 6 UFO sources | done | `sources/*.ufo` x3 (626 glyphs), layout kept as raw GDEF/GSUB/GPOS snapshots (extracted .fea does not recompile) |
| 7 round trip | done at outline level | 626/626 glyphs identical (coords, flags, advances, composites) x3 masters (`reports/session1/ufo_roundtrip.json`); 244 composites lose the OVERLAP_COMPOUND hint bit; production build still runs from baseline binaries |
| 8 scorer-lock CI check | done | `tools/verify_scorer_lock.py`, negative-tested (modified file, extra file -> exit 1) |
| 9 issues | partial | 24 gate + 52 glyph issue specs in `reports/issues/issues.json`; `python tools/create_issues.py` needs a GitHub token. **0 issues created.** |
| 10 CONTRACT_98.md | done | committed before any screenshot measurement (git log order) |
| 11, 16, 17, 18, 21, 22, 23, 26 (Phase B, partial) | partial | `reference/CAPTURE_PROTOCOL.md` (draft), 334 glyph bitmaps + overlays, per-glyph measurements, provisional IoU + heatmaps + ranking, `reference/README.md` |

Also found: the frozen reproducibility claim only held inside the original sandbox (7/7 binaries mismatched on any other machine); Font Bakery now measured.

## 2. Score table (CONTRACT_98 rubric; points earned only when a script's number meets the full-marks rule)
| component | pts | evidence | result |
|---|---|---|---|
| Shape IoU | 20 | `reports/session1/glyph_iou.json` (provisional method, proposal D) | NOT MEASURED under the contract (provisional: letters median 0.828, 41/52 below 0.88) |
| Glyph widths | 8 | `capture_measurements.json`; frozen scorer 68/79 within 1 px | FAIL: 72/79 = 91.1% within 0.5 px, need 98% |
| Held-out pair gaps | 10 | frozen scorer 40/49 within 1 px (81.6%); held-out membership of those pairs unverified | FAIL, need 95% |
| Vertical metrics | 5 | frozen scorer 8/9 (Q below baseline) in Regular, 8/9 Medium, 8/9 SemiBold | FAIL |
| Stems | 7 | same-method re-measure: 5/10 within 5%, 3/10 within 3%, Regular only | FAIL (Regular); 600/700 NOT MEASURED |
| String render match | 5 | none | NOT MEASURED |
| Font Bakery | 8 | `bakery_universal_*.txt`: 2 FAIL on all 4 files (nested components uni013F/uni0140/uni1ECB; Mac name records) | FAIL |
| Coverage | 4 | contract gate 3 | PARTIAL |
| Confusables | 5 | `tools/confusables.py`: default mode FAIL (I~l 1.00, rn~m 0.75), ss13+zero mode all 7 pass | evidenced; PASS only if amendment B is approved |
| Kerning review | 5 | none | NOT DONE |
| Engines and OS | 7 | none | NOT MEASURED |
| Real screens | 6 | none | NOT DONE |
| Name clearance | 4 | decision open | NOT DONE |
| Legal/originality | 3 | none | NOT DONE |
| Distinct from Instrument Sans | 3 | none | NOT DONE |

Evidenced points: widths 8 + pair gaps 10 + vertical 5 + confusables 5 = **28 of 100**. Earned: 0.

## 3. Glyphs touched
None. Phase C has not started (rule 5). Baseline per-glyph IoU (provisional, Regular, mean of 3 sizes), lowest letters: J 0.35, K 0.55, R 0.66, Y 0.67, y 0.68, a 0.72, k 0.74, v 0.76. Full ranking `reports/diffs/RANKING.md`, heatmaps `reports/diffs/u<HEX>.png`. Width and vertical error per glyph: `reports/session1/capture_measurements.json`.

## 4. Worst 5 remaining gaps (numbers from scripts)
1. **Shape**: letters median IoU 0.828, 41 of 52 below 0.88; J 0.35, K 0.55, R 0.66, Y 0.67; reference `3` has a flat top bar.
2. **Weight/stroke**: reference is monolinear (vertical/horizontal stem 0.997) but Synthetix is 1.135; Regular vertical stems 16.6% heavier. Medium and SemiBold stems differ by glyph (H vs l).
3. **Widths**: 7 glyphs outside 0.5 px; largest `-` -1.33 px and `(` -1.09 px at 16 px.
4. **Spacing**: `)/` -2.28 px at 16 px is the largest of 106 pairs; punctuation pairs carry most of the spread (letters are within about 0.2 px).
5. **Quality gates**: Font Bakery 2 FAIL per file, no cross-engine, device, or review evidence.

## 5. Blockers
* **Nothing is on GitHub yet.** The sandbox has no git credentials. Needs one action from you (see NEEDS_FROM_DANIEL #1).
* Amendments A-D need your decision before the affected components can be scored.
* Phase B needs more captures (SemiBold, Bold, heading, big digits, dark mode, punctuation in real strings).
* CI never ran on GitHub; devcontainer never built.

## 6. Next 3 actions
1. Push the branch (bundle supplied), run `python tools/create_issues.py`, trigger the CI run and read the result.
2. Approve or reject amendments A-D in `reports/AMENDMENTS.md`.
3. Provide the re-captures in NEEDS_FROM_DANIEL #3 so steps 12-14, 19, 24 and 25 can finish; then write `reference/dna/<glyph>.json` for the 10 lowest glyphs (step 20) and start Phase C on J.
