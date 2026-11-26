# Synthetix UI: path to 98/100 and 9.9/10 (107 steps)

Written after reading the repo: README, CONTRACT_10_10, V4_REPORT, CONTRACT_STATUS, GLYPH_DECISION_REGISTER, IDENTITY_DIRECTION, CHANGELOG, tools/ (tune_glyphs, build_fork, fit_font, fork_params) and metrics/pinterest-sans-measured.json. Every step runs in Codespaces/CI with Copilot or Claude, and says what score it moves.

## 1. What the font is today (why it is not looking right)

- Synthetix UI is Instrument Sans outlines plus proportion edits. tools/tune_glyphs.py only scales letter widths about the ink centre, stretches ascenders/descenders and lifts i/j dots. Weights are interpolated from Instrument Sans Regular/Bold, tracking is baked in. **No letter has been redrawn.** 485 of 502 V3 glyphs are byte-identical to the base.

- Scaling fixes width, never shape. That is why shape IoU is 31/52 = 59.6%. Below 0.85: J .44, K .63, Q .71, i .71, R .74, a .75, y .75, Y .76, G .77, g .77, C .78, r .80, c .80, j .81, S .82, X .82, w .82, e .83, k .83, U and s just under .85.

- Other failures: widths 68/79 (J r ! ( ) / - : ; , .), pair gaps 40/49 and not held out, vertical 8/9 (Q tail), stems 9/11 on Regular only. Never run: Font Bakery, Firefox, WebKit, devices, human reviews. Contract: 6 of 24 items pass.

- The GitHub repo holds docs plus 5 old V2 tools. fonts/ has no binaries; tools/scorer, reference/, baseline/ exist only in synthetix-ui-v4.zip. Nothing can be rebuilt or scored from GitHub today.

- Ground truth is thin: one set of screenshots, no held-out split, glyph bitmaps missing.

## 2. How 98/100 and 9.9/10 are defined

The contract refuses to print a 0-100 number. This rubric is committed as CONTRACT_98.md before any new measurement (same rule as V4: thresholds never move after seeing results). Full marks need the 98-tier threshold, which is stricter than the contract's.

| Component | Pts | Full marks when |
| --- | --- | --- |
| Shape IoU vs reference | 20 | median >= 0.93 and every Match glyph >= 0.88 |
| Glyph widths | 8 | within 0.5 px on >= 98% (letters, digits, punctuation) |
| Held-out pair gaps | 10 | within 1 px on >= 95% of held-out pairs |
| Vertical metrics | 5 | all within 1 px, every weight |
| Stems | 7 | within 3% in 400/600/700 from real references |
| String render match | 5 | blur-normalised SSIM >= 0.95 on held-out UI strings, 3 sizes |
| Font Bakery | 8 | 0 FAIL on every shipped file |
| Coverage | 4 | all 324 Latin Core + official African list |
| Confusables | 5 | all 7 pairs <= 0.65 |
| Kerning review | 5 | named pairs approved by 2 reviewers |
| Engines and OS | 7 | Chromium, Firefox, WebKit, Android, iOS/CoreText, Windows agree |
| Real screens | 6 | one per platform |
| Name clearance | 4 | decision made, registries searched |
| Legal/originality review | 3 | consult recorded |
| Distinct from Instrument Sans | 3 | blind review passes |

Fidelity = 55 pts, Quality = 35, Identity/legal = 10. **Likeness /10 = 10 x fidelity pts / 55**, so 9.9 needs >= 54.5 of 55. **98/100 allows 2 points of slack in total.**

Two amendments, recorded openly (not waivers): (a) the blind review compares Synthetix to Instrument Sans only, because "identical to the target" and "reviewers can tell it from the target" cannot both be goals; (b) confusables are scored in ID mode (ss13 + zero) as V4 decision 5 proposes, since the reference's own I and l are near-identical (0.133 vs 0.126 cap).

Originality line: likeness comes from measured proportions and outlines drawn from measured specs. Never trace or extract the reference font. This matches your IDENTITY_DIRECTION.md; step 102 is the legal check.

## 3. The 107 steps

### A. Foundation (1-10)

- **1.** Unzip synthetix-ui-v4.zip over a fresh clone and push with git (the connector cannot push binaries): fonts, tools/scorer, baseline/v3, reference, tokens. Why: nothing builds or scores from GitHub today.

- **2.** Add .github/copilot-instructions.md and a Claude Project instruction file: the contract, "never edit tools/scorer", "never change thresholds", "every glyph change reports IoU before and after". Why: stops AI tools drifting or relaxing gates.

- **3.** Devcontainer: Python 3.12, fonttools, fontmake, ufo2ft, extractor, ufoLib2, skia-pathops, booleanOperations, numpy, scikit-image, opencv-headless, cma, uharfbuzz, fontbakery, gftools, ttfautohint, playwright. Why: V4 ran offline, so Bakery, ttfautohint, brotli, Firefox and WebKit never ran.

- **4.** pip install brotli, rebuild WOFF2. Why: reproducibility stops depending on the Node shim.

- **5.** Run .github/workflows/ci.yml for the first time and fix until green. Why: it was never executed; every gate needs a machine other than your sandbox.

- **6.** Convert the V4 TTFs to UFO sources (extractor package) with a 3-master designspace. Why: redraws must happen in editable sources, not by patching compiled TTFs.

- **7.** Build from UFO with fontmake; tools/check_regression.py must show the 485 untouched glyphs byte-identical. Why: proves the new pipeline loses nothing.

- **8.** CI fails if any hash in reports/scorer.lock.json changes. Why: nobody edits the judge.

- **9.** One GitHub Issue per gate (24) and per Match glyph (52), scorer number as acceptance. Why: small, verifiable tasks for Copilot/Claude.

- **10.** Commit CONTRACT_98.md (section 2) before measuring anything new. Why: a 98 whose goalposts cannot move.

### B. Ground truth (11-26)

- **11.** Write reference/CAPTURE_PROTOCOL.md: device, app version, DPR, language, light and dark, no zoom, PNG only. Why: every later number is only as good as the captures.

- **12.** Re-capture Pinterest UI at three cap sizes (about 45, 49, 57 px) plus heading (~70) and big digits (~126), in Regular, SemiBold, Bold. Why: three scales per glyph for consistency checks, plus real Bold evidence.

- **13.** Capture punctuation and digits inside real strings: ! ? , . : ; ( ) / - & @ # % 0-9. Why: ( ) / - : ; have no per-glyph reference and are most of the 11 failing widths.

- **14.** Capture every letter in at least 3 words (start, middle, end), plus Hausa/Yoruba/Igbo text if the app shows it. Why: clean crops need letters that do not touch.

- **15.** Split texts 70/30 into reference/split.json (fit vs held-out), hash-pinned in the scorer lock. Why: today's gap score (81.6%) was fitted on its own test pairs; this makes it honest.

- **16.** Cut per-glyph bitmaps by connected components, aligned on baseline and cap line, with overlay images for manual QA. Why: IoU needs real bitmaps and they are missing.

- **17.** Normalise each crop to cap = 1.0, save reference/glyphs/<char>_<size>.png. Why: shapes comparable across sizes and fonts.

- **18.** Re-measure per glyph per size: ink width, left/right edges, vertical and horizontal stem, x-height, ascender, descender; keep medians. Why: medians cancel antialias noise.

- **19.** Reject any glyph whose measurement varies more than 3% across sizes and recapture. Why: bad ground truth trains the optimiser toward noise.

- **20.** Write reference/dna/<glyph>.json: terminal cut angles (t r f j y J), apertures (c e a s C G S), bowl widths, arch junction (n m h), tail form (Q y J g), dot diameter (i j). Why: turns "looks different" into numbers an AI tool can solve for.

- **21.** Re-run the frozen scorer on V4 with the new bitmaps. Why: a real baseline replaces carried-over V3 numbers.

- **22.** Generate XOR heatmaps (red = extra ink, blue = missing ink) per glyph into reports/diffs/. Why: Copilot/Claude can see exactly where each shape deviates.

- **23.** Rank glyphs by IoU gap x letter frequency in UI text (English plus Hausa, Yoruba, Igbo). Why: fix what users see most first.

- **24.** Add real SemiBold and Bold bitmaps and stems to the scorer inputs. Why: closes the stems line that is FAIL/NOT MEASURABLE now.

- **25.** Capture the same strings in dark mode. Why: dark-theme stems look thinner; needed for the weight check in step 80.

- **26.** Version the captures in reference/README.md with dates and hashes, never overwritten. Why: reproducible evidence.

### C. Letter-by-letter redraw (27-63)

- **27.** Write tools/glyph_dna.py: build outlines from DNA specs (skeleton, monoline stem, terminal cuts, overshoot) using designer conventions: points at extrema, horizontal/vertical handles, minimal points, smooth curves. Why: constructed glyphs look drawn, not scaled.

- **28.** Per-glyph optimiser (CMA-ES, cma package): tune DNA parameters to maximise IoU across all three sizes, penalising departure from design rules. Why: replaces eyeballing with search.

- **29.** Acceptance gate per redraw: IoU up, width within 0.5 px, no overlaps, correct contour direction, interpolation-compatible across masters. Why: no redraw can regress something else.

- **30.** Rasterise every candidate at 12-24 px with FreeType as well as Chromium. Why: UI-size rendering is what is judged.

- **31.** **J** (.44, worst): reference ink 0.616 cap; default is about 4 px narrow at cap 49 and J.ss08 about 2.4 px wide. Redraw hook radius and terminal to land on 0.616. Moves shape and width.

- **32.** **K** (.63): ink .754 cap; K.ss04 is 3.9 px too wide. Redraw arm and leg junction on the stem.

- **33.** **Q** (.71): ink 1.0 cap (equals O); reference tail drops about 5 px at cap 49, ss09 drops 8.8. Redraw a shorter tail at the measured angle. Fixes the one failing vertical metric.

- **34.** **i** (.71): dot is 9 px at body cap 56 (0.16 cap) and 16 px at heading size; set dot size per weight, centre and lift from DNA.

- **35.** **R** (.74): ink .708; fit bowl-to-leg junction and leg angle from the heatmap.

- **36.** **a** (.75): double-story, ink .656; fit bowl, top arc and tail. a.ss02 is 1.5 px wide, check as donor.

- **37.** **y** (.75): reference has a straight tail; ink .688, descender .259 cap. Redraw the tail straight.

- **38.** **Y** (.76): ink .809; fit arm junction height.

- **39.** **G** (.77): ink .921; fit bar and spur.

- **40.** **g** (.77): single-story; ink .685, descender .259 cap; fit hook terminal.

- **41.** **C** (.78): ink .907; fit terminal cuts and aperture.

- **42.** **r** (.80): ink .364 (width fails today); fit arm length and terminal cut.

- **43.** **c** (.80): ink .662; fit aperture and terminals.

- **44.** **j** (.81): ink .291; descender .259 cap; dot per step 34.

- **45.** **S** (.82): ink .762; fit spine angle and terminals.

- **46.** **X** (.82): ink .881; fit crossing point.

- **47.** **w** (.82): ink 1.09; fit middle apex height and vertices.

- **48.** **e** (.83): ink .685; fit bar height and terminal.

- **49.** **k** (.83): ink .629; fit arm and leg junction.

- **50.** **U** (about .85): ink .801; fit bottom curve and stem join.

- **51.** **s** (about .85): ink .596; fit spine and terminals.

- **52.** Push the other 31 letters from >= 0.85 to >= 0.92 with the same optimiser. Why: the 98-tier needs median 0.93; the contract's 0.85 is not enough for 9.9.

- **53.** **t**: angled cut top-left, ink .431; redraw per reference. Why: it is in the reference notes and appears in almost every string.

- **54.** Digits 0-9: match measured widths (0 .756, 1 .356, 2 .667, 3 .689, 4 .778, 5 .667, 6 .733, 7 .689, 8 .711, 9 .733 of cap) and shapes from the digit captures. Why: digits dominate commerce UIs.

- **55.** Punctuation ! ? , . : ; ( ) / - & @ # %: widths and shapes from step 13. Why: fixes the punctuation width failures.

- **56.** Round geometry per weight: o width / x-height 1.004, n width / x-height .878 (Regular); 1.024 / .902 (SemiBold); 1.019 / .923 (Bold).

- **57.** Measure overshoot of round vs flat tops from the references; set it per weight.

- **58.** One terminal-cut rule library (t r f j y J), applied identically in every weight. Why: consistent DNA reads as one family.

- **59.** Rebuild SemiBold and Bold by redrawing to stems .1434 and .1786 of cap (Regular .1173), not by interpolating Instrument Sans. Why: stems and shapes match in every weight.

- **60.** Add the 700 Bold master (variable 400-700). Why: Bold evidence now exists; V4 left it out for lack of it.

- **61.** Set vertical metrics exactly per weight: x-height .7289/.7248/.7324, ascender 1.0357/1.0302/1.0423, descender .2485/.2372/.2394 of cap. Why: vertical gate within 1 px.

- **62.** Redraw hooks and open letters (Ɓ Ɗ Ƙ Ƴ ɓ ɗ ƙ ƴ, Ɛ ɛ Ɔ ɔ, ₦, ₹) with the DNA builder and get a native Hausa/Yoruba/Igbo reader to approve. Why: today they are mechanical and unreviewed.

- **63.** Re-run scorer and heatmaps for the full set; tag a checkpoint.

### D. Spacing, kerning, metrics (64-76)

- **64.** Fit per-glyph left/right sidebearings by ridge-regularised least squares on training strings' glyph_left_px. Why: extends your 2-coefficient tracking fit to every glyph.

- **65.** Keep a sidebearing change only if held-out error drops. Why: stops overfitting.

- **66.** Fit class kerning (round, straight, diagonal, open) then exceptions, validated held-out. Why: pair gaps 81.6% toward >= 95%.

- **67.** Check every measured pair plus new pairs from the new captures within 1 px.

- **68.** Re-fit weight tracking a0, a1 after the redraws.

- **69.** Fit word space and punctuation spacing (fit_font.py already solves word spacing).

- **70.** Keep default figures proportional like the reference; tabular stays opt-in. Confirm ₦ columns still align.

- **71.** Recompute size-adjust and fallback metrics for CSS.

- **72.** Build the named-pair sheet (AV, To, Ty, r., Yo, LT, 11 ...) for human review (step 103).

- **73.** Lock hhea/typo/win metrics so every weight is within 1 px of reference; confirm no Windows clipping.

- **74.** Regression-run symbols and African glyphs: untouched outputs stay identical.

- **75.** Gate: widths within 0.5 px on >= 98% of glyphs.

- **76.** Re-run gaps on held-out pairs only; log per pair.

### E. Render-level match (77-86)

- **77.** Write tools/render_match.py: render every held-out reference string with Synthetix at matched cap px (Chromium and FreeType), blur both (sigma about 0.6 px), score SSIM and ink XOR. Why: the pixel-level test of "looks identical", not self-graded.

- **78.** CI artifact gallery per string: reference | ours | diff.

- **79.** Match rasteriser settings to the reference platform (grayscale AA, no hinting) before comparing. Why: stops measuring rasteriser differences.

- **80.** Dark-mode check; adjust weight only if stems differ by more than 3%.

- **81.** 12-14 px legibility sheet for review.

- **82.** Add a calt for rn loosened by <= 0.6 px (inside the 1 px gap tolerance) so rn~m drops under 0.65 in default text.

- **83.** Keep default I and l reference-matching; ship ss13 as the ID mode and score confusables there (amendment b, V4 decision 5).

- **84.** Pass criterion: SSIM >= 0.95 on held-out strings at all three sizes.

- **85.** Take the 10 worst strings, trace each to a glyph or spacing cause, loop back to steps 27 and 64.

- **86.** Freeze the render-match score at a checkpoint tag.

### F. Quality gates, identity, release (87-107)

- **87.** Font Bakery (universal + googlefonts profiles) in CI on every shipped file; a script feeds the JSON report to Copilot/Claude; loop until 0 FAIL. Hard gate.

- **88.** Apply Bakery's metadata fixes (name table, STAT, fvar instances, OS/2, post) with gftools fix-* scripts.

- **89.** ttfautohint plus gasp for Windows at 12-16 px. Why: V4 is unhinted.

- **90.** Install the glyphsets package; check all 324 Latin Core glyphs including the 104 non-letters; add /idotaccent (Lithuanian), ſ and ƒ.

- **91.** Check the official African glyph list from glyphsets instead of the Hausa/Yoruba/Igbo proxy. Why: V4 could not find it offline.

- **92.** uharfbuzz shaping tests for NFC/NFD/reversed marks in all weights, not Chromium only.

- **93.** Playwright on Chromium, Firefox, WebKit: widths on 200 strings, tolerance 0.01 px.

- **94.** windows-latest runner: Edge/DirectWrite screenshot; confirm no clipping.

- **95.** macos runner: CoreText render plus an iOS-simulator SwiftUI test app built from the tokens; compare widths.

- **96.** Android emulator in CI (reactivecircus/android-emulator-runner) with a Compose test app; compare widths and screenshot.

- **97.** Physical devices: one low-end Android (Tecno/Infinix class), one iPhone, one Windows laptop, same test sheet.

- **98.** Subset budget: variable latin 50,192 B to <= 45,000 B by dropping non-core GSUB and hinting tables from the web subset, or ship the 40,128 B lite subset (V4 decision 6).

- **99.** Token adoption on one real screen per platform: web (your Stackra merchant dashboard), Android Compose, iOS SwiftUI; commit screenshots.

- **100.** Native-speaker review of Hausa/Yoruba/Igbo sample text with diacritics at 12-24 px.

- **101.** Rename "Synthetix" (DeFi collision): shortlist 10, search USPTO, WIPO Global Brand DB, Nigeria's trademark registry, domains, npm, GitHub; check Instrument Sans' OFL for a Reserved Font Name; rename in name IDs, CSS, files, docs. Why: the critical defect that blocks "zero critical defects".

- **102.** One IP-lawyer consult on a measured-proportion face with original outlines; record in NAME_CLEARANCE.md.

- **103.** Send the named-pair sheet to two reviewers via a form; record results.

- **104.** Blind identity review per IDENTITY_DIRECTION (Synthetix vs Instrument Sans) with NSUK design students and Nigerian design communities; record in reports/identity_review.json.

- **105.** Regenerate CONTRACT_STATUS and a 100-point scorecard JSON via tools/contract_check.py; it prints no total unless every component's evidence file exists.

- **106.** Clean-clone build on a different CI machine; SHA-256s must match; tag the release.

- **107.** Score-regression guard: any drop in any component fails the PR; keep reference captures versioned.

## 4. Why this lands at 98 and 9.9

- IoU is area overlap. Only changing outlines moves it, and steps 27-52 change outlines against a measurable objective (reference bitmaps, three sizes, held-out check), not by eye.

- Each fidelity point has named steps behind it: shape 20 (16-23, 27-52), widths 8 (13, 54-55, 75), gaps 10 (15, 64-67, 76), vertical 5 (33, 61, 73), stems 7 (12, 24, 59-60), render match 5 (77-86).

- Quality items are infrastructure, not craft: Bakery, engines, hinting, budgets all run in CI once the network exists (steps 3-5).

- Identity and legal points are decisions and reviews: name, lawyer, two reviewers.

- 9.9 means at most 0.55 of the 55 fidelity points lost, so every fidelity component must be near full. The held-out split and the frozen scorer mean the number cannot be inflated.

## 5. What only you can supply

- Screenshots from your phone (steps 11-14, 25): about 1-2 hours; unlocks most of the 55 fidelity points.

- Two reviewers plus one native-language reader (steps 100, 103, 104).

- The name decision and a lawyer slot (101, 102).

- Eye-approval of redraws (hooks, Ɛ, ₹) as they land.

Everything else is code and CI.
