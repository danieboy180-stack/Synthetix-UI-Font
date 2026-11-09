# V4.0.10 report — read this first

**Verdict: not 10/10.** This is a release candidate. Of the contract's 24 line items, 6 pass, 8 fail, 9 are not measured or not done, and 1 (name clearance) is recorded with the decision open (`reports/CONTRACT_STATUS.md`).
Several of the failures cannot be fixed without inputs this run did not have (reference screenshots, Font Bakery, Firefox/WebKit, devices, two human reviewers). I did not estimate or relax any of them. "No errors and no flaws" cannot honestly be claimed; the known ones are listed below.

## 1. Regressions first
- **None found in what V3 measured.** The regression ledger (`reports/regression_ledger.json`) compares all 502 V3 glyphs in all three masters: 485 are byte-identical (outline, advance, sidebearing), 17 tabular figures were only re-centred, glyph IDs are stable, 0 violations. The frozen scorer returns exactly V3's numbers on Regular (widths 68/79, vertical 8/9, gaps 40/49, stems 9/11).
- Things that got worse or were *introduced*: the variable build's latin subset is 51,232 B against a 45,000 B budget registered before export (static subsets all pass); `multiply.tf` is 10/16/26 units narrower; Medium/SemiBold scorer width/gap numbers look poor (60/79, 9/79) only because the only reference is Regular — they are not defects and are not comparable.

## 2. What V4 adds (all verified unless marked)
| Area | Result |
|---|---|
| Pri-African Latin + U+0323 + tone stacking | 192 NFC/NFD/reversed-order renders identical across Regular, SemiBold, variable (Chromium) |
| Numerals | tabular figures exactly equal (static + 7 variable instances; money columns align with ₦); `zero`, `lnum`, `frac`, `numr/dnom`, `sups/subs/sinf`, fractions |
| Coverage | Latin-1 and Latin Ext-A complete except ſ (U+017F) and ƒ (U+0192); Tier-3 UI symbols present |
| Variable font | wght 400–600 (three evidence-backed masters; **no 700** because there is no Bold evidence), static agreement ≤ 0.5 unit, STAT, named instances |
| Reproducibility | 27/27 font files identical from a clean copy under two hash seeds. Found and fixed a wall-clock `head.modified` in the variable build |
| Exports | TTF, WOFF, WOFF2, 4 unicode-range subsets; fallback metrics (size-adjust 103.6%) |
| Tokens | W3C JSON → CSS/Swift/Android; 22 WCAG AA contrast pairs pass (palette is a placeholder) |
| Inherited defect fixed | `usWinDescent` 300 vs comma-below −329 (SemiBold) |
| Confusables | `ss13` + `zero` separates Il1/O0 (worst Jaccard 0.60 ≤ 0.65); default I~l = 1.00 and rn~m = 0.75 **fail** the pre-registered threshold; rn~m also fails with ss13 |

## 3. Why it is not 10/10 (and what unblocks each)
1. **Fidelity** (all below threshold): shape IoU ≥ 0.85 on 31/52 letters = 59.6% (recorded V3 values, carried over because outlines are unchanged); widths 86.1% (68/79; failing J r ! ( ) / - : ; , .); pair gaps 81.6% and not held out; vertical 8/9 (Q tail); stems 9/11 on Regular, heavier weights have no real references. *Needs:* reference screenshots at three cap scales with a held-out split (Stages 3–4), then glyph redraws approved by you.
2. **Font Bakery** 0 FAIL: not run (not installed, no network). *Needs:* CI — `.github/workflows/ci.yml` (never executed).
3. **Other engines/devices:** only Chromium ran. *Needs:* Firefox/WebKit (CI), iOS/Android test apps, Windows.
4. **People:** identity blind review, kerning-pair review, token adoption on real screens.
5. **Stage 2 is partial:** the build is reproducible from the frozen V3 *binaries*, not from upstream Instrument Sans sources (no network), so source-level repair did not happen.
6. **Name:** "Synthetix" collides with an established DeFi protocol (`NAME_CLEARANCE.md`).

## 4. Known flaws in new work
New glyph designs are constructed from primitives, not drawn by a type designer: hooks on Ɓ/Ɗ/Ƙ/Ƴ and ɓ/ɗ/ƙ/ƴ are mechanical, Ɛ/ɛ and Ɔ/ɔ are approximations, ₹ is crude, superior/inferior figures are scaled with compensation and read slightly heavy, tail of ss13 `l` is a plain curl. Inherited kerning is copied from a "parent" letter for new glyphs, not tuned. Variable-font win metrics are constant. Hinting: unhinted (ttfautohint unavailable). Native/CI files are unverified.

## 5. Decisions needed from you
(1) Rename or keep the working title. (2) Confirm or override the proposed Match/Keep/Diverge register and give your priority glyph list. (3) Send reference screenshots if you want Stages 3–4. (4) Approve or reject hook/Ɛ/₹ designs by eye. (5) Decide whether ss13 should be promoted for IDs in product UIs.

## 6. Reproduce
`README.md` → "Build and verify". Environment: `reports/build-environment.json` (fontTools 4.67.0, Node brotli shim because `pip brotli` was unavailable).
